#!/usr/bin/env python3
"""wrong-answer-cell-power-fix -- Arm A extraction (GPU): deployment-render
hidden-state backfill over the full 3369-row scored population, both
checkpoints in one pass.

Pre-registered in experiments/wrong-answer-cell-power-fix/AMENDMENT.md (SIGNED),
section 2.3. Instrument pinned in cell.yaml (sha256 5ee37dd3..., verified at
import time below) and gates.yaml (sha256 01ee0b01...). THE SPEC IS LOCKED: this
module reads cell.yaml, it does not restate or override any of its values.

WHAT THIS DOES. No generation -- the deployment-rendered generations already
exist (the two scored_rows.jsonl files cell.yaml pins) and are already graded.
This is a single base-vs-LoRA forward pass per row, reusing the common
crash-safe extraction harness (experiments/common/knowledge_probe/
hidden_state_probe.py + friends) as a LIBRARY:

  - h_base (adapter DISABLED)  == the "cleansft" checkpoint's hidden state
  - h_lora (adapter ACTIVE)    == the "grpov2" checkpoint's hidden state

Both checkpoints share the identical merged-16bit base weights and the run
differs only in whether the GRPO-v2 LoRA is applied, which is exactly the
base_arm/active_arm contrast hidden_state_probe.py's extraction loop is built
around (AMENDMENT.md section 2.3: "the clean-SFT control checkpoint is read
from h_base in the same pass at no extra GPU cost"). This module supplies a NEW
selection (slice_rows over the full deployment-rendered 3369-row population,
joined from the two scored_rows.jsonl files via row_join.py) and a NEW system
prompt (the deployment eval render, read verbatim from its source config, not
hardcoded here); everything else -- config validation, crash-safe manifest,
resumable append-log, safetensors persistence, layer_list filtering -- is the
existing common harness, imported unmodified.

TWO ENTRY MODES:
  --check   CPU-only, torch-free. Builds the config + slice_rows, runs every
            model-free validation (schema.validate_arm_states, G0-2 join
            integrity), and prints a summary. Never imports torch/transformers/
            peft. Safe to run anywhere, any time, no GPU.
  --run     The real GPU extraction (hidden_state_probe.build_extraction_backend
            + run_extraction). Loads both checkpoints, forwards every row twice
            (base, active), and persists h_base/h_lora safetensors under
            analysis/hidden_states/ (gitignored). NOT invoked by the harness
            builder; launch is lead-gated per AMENDMENT.md.

Neither mode ever prints or persists question text, generated_answer,
answer_text, or aliases (containment: AMENDMENT.md section 7).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

EXP_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXP_DIR.parents[1]

# Reuse the shared readouts path helper (experiments/common/readouts/path_compat.py)
# instead of re-deriving repo-root detection; see amendment_s/t precedent.
READOUTS_DIR = REPO_ROOT / "experiments" / "common" / "readouts"
if str(READOUTS_DIR) not in sys.path:
    sys.path.insert(0, str(READOUTS_DIR))
from path_compat import knowledge_probe_dir  # noqa: E402

PROBE_DIR = knowledge_probe_dir()
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))
if str(EXP_DIR) not in sys.path:
    sys.path.insert(0, str(EXP_DIR))

import row_join  # noqa: E402  (this experiment dir)

CELL_YAML = EXP_DIR / "cell.yaml"
CELL_YAML_SHA256_PINNED = (
    "5ee37dd3bdb12e64dd526441f34e732d241e11fbd9c6841879d51ae3ed7b6b34"
)
GATES_YAML_SHA256_PINNED = (
    "01ee0b017009cf6298a77c60fb5e2a82a67324c1bc0a7d4398489ee1bad2cc54"
)


def _assert_cell_yaml_unmodified() -> dict:
    """Load cell.yaml and hard-fail if it drifted from the experiment.yaml pin.

    THE SPEC IS LOCKED: this is a belt-and-suspenders integrity check (not one
    of the named G0/E gates), so a hand-edit of the pinned instrument config
    aborts every downstream script immediately instead of silently running
    against a different spec than the one that was signed.
    """
    got = row_join.file_sha256(CELL_YAML)
    if got != CELL_YAML_SHA256_PINNED:
        raise RuntimeError(
            f"cell.yaml sha256 {got} != pinned {CELL_YAML_SHA256_PINNED} "
            "(experiment.yaml instrument.pins); THE SPEC IS LOCKED -- refusing "
            "to run against a modified pinned config"
        )
    with CELL_YAML.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_deployment_system_prompt(cell: dict) -> str:
    """Read the deployment eval render's prompt.system VERBATIM from its source
    config (cell.yaml render.deployment_eval_prompt), sha-verifying the source
    file against cell.yaml's pinned source_sha256 first. Never hardcoded here,
    so this cannot drift from the eval config that produced the scored rows.
    """
    block = cell["render"]["deployment_eval_prompt"]
    source_path = REPO_ROOT / block["source"]
    got_sha = row_join.file_sha256(source_path)
    expected_sha = block["source_sha256"]
    if got_sha != expected_sha:
        raise RuntimeError(
            f"deployment eval config sha256 {got_sha} != cell.yaml-pinned "
            f"{expected_sha} ({source_path}); refusing to render under a "
            "drifted prompt source"
        )
    with source_path.open(encoding="utf-8") as fh:
        eval_cfg = yaml.safe_load(fh)
    key_path = block["source_key"].split(".")
    node = eval_cfg
    for key in key_path:
        node = node[key]
    if not isinstance(node, str) or not node.strip():
        raise RuntimeError(f"{block['source_key']} at {source_path} is empty/not a string")
    return node


def build_join(cell: dict) -> row_join.JoinResult:
    checkpoints = {c["id"]: c for c in cell["arm_a"]["checkpoints"]}
    grpov2 = checkpoints["grpov2"]
    cleansft = checkpoints["cleansft"]
    return row_join.build_join(
        REPO_ROOT / grpov2["scored_rows"],
        REPO_ROOT / cleansft["scored_rows"],
        expected_grpov2_sha256=grpov2["scored_rows_sha256"],
        expected_cleansft_sha256=cleansft["scored_rows_sha256"],
    )


def build_extraction_config(cell: dict, system_prompt: str,
                             grpov2_sha: str, cleansft_sha: str) -> dict:
    """Assemble the hidden_state_probe.py config dict for this Arm A pass.

    Every value traces to cell.yaml (arm_a.checkpoints / arm_a.extraction);
    nothing here is a new design decision. `selection` is set to the
    `probe_pool` shape ONLY so hidden_state_probe.collect_static_provenance's
    `selection_data_source` resolves to a real, sha-meaningful file for the
    manifest's `data_sha256` field -- this module does NOT call
    select_matched_slice (the slice_rows come from row_join.build_join, below).
    """
    checkpoints = {c["id"]: c for c in cell["arm_a"]["checkpoints"]}
    grpov2 = checkpoints["grpov2"]
    cleansft = checkpoints["cleansft"]
    extraction = cell["arm_a"]["extraction"]
    if grpov2["base"] != cleansft["base"]:
        raise ValueError(
            "arm_a checkpoints do not share a base model; the one-pass "
            "h_base==cleansft / h_lora==grpov2 equivalence does not hold"
        )
    base_model_path = str(REPO_ROOT / grpov2["base"])
    adapter_path = str(REPO_ROOT / grpov2["adapter"])

    return {
        "model": {
            "model_name": base_model_path,
            "model_tag": "wrong-answer-cell-power-fix-arm-a",
            "enable_thinking": extraction["enable_thinking"],
            "revision": None,
        },
        "arms": [
            {"name": "cleansft", "adapter": None, "adapter_state": "disabled"},
            {"name": "grpov2", "adapter": adapter_path, "adapter_state": "active"},
        ],
        "extraction": {
            "device": "cuda",
            "token_position_rule": extraction["token_position_rule"],
            "layer_list": list(extraction["layer_list"]),
            "compute_dtype": extraction["compute_dtype"],
            "persist_dtype": extraction["persist_dtype"],
            "persistence_format": extraction["persistence_format"],
            # cell.yaml arm_a.extraction.persist == [h_base, h_lora] only; the
            # common harness's third role (delta) is opt-out via persist_delta.
            "persist_delta": False,
            "granularity": "residual_stream",
        },
        "output": {
            "root": "experiments/wrong-answer-cell-power-fix/analysis/hidden_states",
            "hidden_states_subdir": "extraction",
            "manifest_filename": "manifest.json",
            "rows_filename": "rows.jsonl",
        },
        "manifest_provenance": {
            "source_split": "selfaware-full-3369-deployment-render",
            "aligned_run_record_id": "wrong-answer-cell-power-fix-arm-a",
        },
        "selection": {
            "source": "probe_pool",
            "probe_results": grpov2["scored_rows"],
        },
        "prompt": {"system": system_prompt},
    }


def build_slice_rows(join: row_join.JoinResult, cell: dict) -> list[dict]:
    """Slice rows for hidden_state_probe.run_extraction: ALL 3369 joined rows
    (AMENDMENT.md decision #9 -- full population, no subsampling), so every
    behavior cell A9 needs is populated.

    `aligned_probe_config_sha` (a REQUIRED-non-null per-row/manifest field in
    the common harness's schema) is stamped with a composite identity over the
    two pinned scored_rows sha256 values -- this is the true join/alignment
    provenance for Arm A, not a probe-tier config (there is no probe tier
    upstream of this cell; see AMENDMENT.md section 2.3).
    """
    aligned_sha = hashlib.sha256(
        f"wrong-answer-cell-power-fix-arm-a:{join.grpov2_sha256}:{join.cleansft_sha256}"
        .encode()
    ).hexdigest()[:16]
    rows = []
    for jr in join.rows:
        rows.append({
            "probe_pool_row_key": jr.row_id,
            "row_key": jr.row_id,
            "question": jr.question,
            "label": jr.grpov2.label,  # SelfAware known/unknown; identical across checkpoints (row_join G0-2 asserts this)
            "probe_label": None,
            "aligned_probe_config_sha": aligned_sha,
        })
    return rows


def parse_arm_a_config(config: dict) -> tuple[dict, str]:
    """Mirror hidden_state_probe.parse_config's body without touching PROBE_DIR
    or select_matched_slice (this cell supplies its own slice_rows). Runs the
    identical model-free pre-flight (P0 adapter-state guard, token-position-rule
    validation) so a malformed config fails before any model load, exactly as
    the common harness's parse_config does for its own callers.
    """
    import hidden_state_schema as schema  # noqa: PLC0415

    schema.validate_arm_states(config["arms"])
    schema.validate_token_position_rule(config["extraction"]["token_position_rule"])
    schema.validate_granularity(
        config["extraction"].get("granularity", schema.GRANULARITY_RESIDUAL_STREAM))
    cfg_sha = schema.config_sha(config)
    return config, cfg_sha


def check(*, quiet: bool = False) -> dict:
    """CPU-only, torch-free build + validate. Returns a summary dict."""
    cell = _assert_cell_yaml_unmodified()
    system_prompt = load_deployment_system_prompt(cell)
    join = build_join(cell)
    if not join.g0_2["pass"]:
        raise RuntimeError(f"G0-2 join integrity FAILED: {json.dumps(join.g0_2, indent=2)}")
    config = build_extraction_config(
        cell, system_prompt, join.grpov2_sha256, join.cleansft_sha256)
    config, cfg_sha = parse_arm_a_config(config)
    slice_rows = build_slice_rows(join, cell)

    import hidden_state_probe as hsp  # noqa: PLC0415  (torch-free import; heavy deps are lazy inside backends)

    out_dir = hsp.resolve_output_dir(config, cfg_sha)

    summary = {
        "cell_yaml_sha256": CELL_YAML_SHA256_PINNED,
        "gates_yaml_sha256_pinned": GATES_YAML_SHA256_PINNED,
        "system_prompt_len_chars": len(system_prompt),
        "system_prompt_sha256": hashlib.sha256(system_prompt.encode()).hexdigest(),
        "n_slice_rows": len(slice_rows),
        "extraction_config_sha": cfg_sha,
        "output_dir": str(out_dir.relative_to(REPO_ROOT)),
        "layer_list": config["extraction"]["layer_list"],
        "persist_delta": config["extraction"]["persist_delta"],
        "g0_2_join_integrity": join.g0_2,
    }
    if not quiet:
        print(json.dumps(summary, indent=2))
    return summary


def run(*, quiet: bool = False) -> Path:
    """The real GPU extraction. NOT called by --check; requires torch/transformers/peft."""
    cell = _assert_cell_yaml_unmodified()
    system_prompt = load_deployment_system_prompt(cell)
    join = build_join(cell)
    if not join.g0_2["pass"]:
        raise RuntimeError(f"G0-2 join integrity FAILED: {json.dumps(join.g0_2, indent=2)}")
    config = build_extraction_config(
        cell, system_prompt, join.grpov2_sha256, join.cleansft_sha256)
    config, cfg_sha = parse_arm_a_config(config)
    slice_rows = build_slice_rows(join, cell)

    import hidden_state_probe as hsp  # noqa: PLC0415

    out_dir = hsp.resolve_output_dir(config, cfg_sha)
    backend = hsp.build_extraction_backend(config, system_prompt)  # GPU load
    manifest_path = hsp.run_extraction(config, cfg_sha, backend, slice_rows, out_dir)
    if not quiet:
        print(f"arm_a_extract: wrote manifest to {manifest_path}")
    return manifest_path


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                       help="CPU-only build+validate; never loads a model")
    mode.add_argument("--run", action="store_true",
                       help="the real GPU extraction (loads both checkpoints)")
    ap.add_argument("--quiet", action="store_true")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.check:
        check(quiet=args.quiet)
        return 0
    run(quiet=args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
