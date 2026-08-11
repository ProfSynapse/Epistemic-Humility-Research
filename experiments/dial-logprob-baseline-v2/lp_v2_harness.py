#!/usr/bin/env python3
"""Dial token-logprob baseline v2 -- generation-time token-ID cache (GPU + CPU).

Registered in experiments/dial-logprob-baseline-v2/AMENDMENT.md. Clean redo of
experiments/dial-logprob-baseline/ (v1, resolved 2026-07-18, verdict
DATA-STAGE STOP): v1 reconstructed answer-span token IDs by re-tokenizing
DECODED text, which is not bit-stable at BPE span boundaries (30/3324 rows,
0.9%, off by exactly one token). THE FIX: capture the exact generation-time
token IDs from ONE `model.generate(..., output_scores=True)` call per row --
never reconstructed, never re-tokenized. Full rationale:
docs/preparation/amendment-draft-dial-logprob-baseline-v2.md sec.3.

WHAT THIS DOES, per arm (S base primary / T deployed descriptive):

  1. Load the arm's model+tokenizer (real path, `load_model_and_tokenizer`) or
     use an injected model+tokenizer (smoke/test path) -- `run_arm` takes
     `model`/`tokenizer`/`device` as parameters precisely so the generation +
     capture logic can be exercised end to end with a tiny CPU model, without
     downloading real weights, in `test_lp_v2_smoke.py`.
  2. For every answered row (label in {correct, wrong}) in the arm's cached
     rows.jsonl: render the prompt with the SAME chat template and system
     prompt the source S/T extractor used (imported by reference from those
     modules' SYSTEM_PROMPT constants -- never retyped, so this harness cannot
     silently drift from the render the cached rows were produced under), and
     regenerate under the SAME decode settings (greedy, max_new_tokens=48,
     batch-1 -- see cell.yaml `generation`). Capture `new_ids` (from
     `gen.sequences`) and per-step logits (`gen.scores`) from that ONE call.
  3. LP-G0 v2 criterion: decode(new_ids) must equal the row's cached
     `answer_text` BYTE-FOR-BYTE. Any mismatch is recorded per-row, never
     silently patched or tolerance-adjusted.
  4. Compute the length-normalized mean (primary), sum, and min (secondary)
     answer-span token logprob directly from `new_ids`/`gen.scores` -- never
     from re-tokenized text. The answer span is the same content-token window
     the source extractor used (`_content_end_index`, imported unchanged).
  5. Persist per-row results incrementally (append + flush) to a resumable
     JSONL runlog under the gitignored analysis/ dir, so a kill mid-arm does
     not lose completed rows. `RunLog` (synaptic-tuner shared/utilities/
     run_log.py, the README-runlog.md convention) is UNAVAILABLE on the
     current submodule pin (branch feature/runlog, not on main as of
     2026-08-11 -- see NOTEBOOK.md); this module reimplements the same
     append+flush+resume contract locally instead of checking out a different
     submodule branch.

Then, per arm (`score_arm`, CPU-only, no model needed):

  6. Dial refit: reuse `oof_probe` / `load_position_layers` from
     amendment_s_correctness_probe_score.py UNCHANGED, on the arm's EXISTING
     cached hidden-state tensors at its pinned dial layer, and assert the
     refit AUROC reproduces the signed source AUROC (LP-G0 sub-criterion,
     unchanged from v1 -- this part never touches generation and needs no
     GPU).
  7. AUROC per logprob variant, and the paired dial-minus-logprob bootstrap
     margin (`paired_bootstrap_delta`, reused unchanged).
  8. LP-G1 gate evaluation (primary arm only) against the verbatim v1
     threshold / ambiguous band / falsifier recorded in gates.yaml.

CLI modes (`main`):

  --dry-run          resolve every real input named in cell.yaml (rows.jsonl
                      paths, tensors_dir, checkpoint/adapter paths, the dial
                      refit module) and print the execution plan; loads no
                      model, computes nothing, writes nothing. Exit 0 iff
                      every input resolved; exit 2 iff any did not -- that IS
                      the check passing (it means the harness correctly
                      detected the repo/data state), not a crash.
  --arm ID            run one arm for real: loads the real model/tokenizer
                      (GPU) and runs the full regenerate+capture+score
                      pipeline. Requires the launch precondition in
                      AMENDMENT.md sec.8 (item-27 GPU tail clear + explicit
                      PI approval); this module does not check or wait for
                      that, it only performs the compute once invoked.
  --arm ID --timing-smoke N
                      generation-only pass over the first N rows of --arm,
                      reports wall clock, skips scoring. Still a GPU touch,
                      still needs the same launch authorization as a full
                      run -- registered as a mode here, NOT invoked by this
                      build task (design draft sec.8 pass 0).

Containment: this module and its outputs never write question/answer/token
content to analysis-committed/; only aggregate JSON, an id-manifest (row_key
list), and per-variant tables are ever eligible for commit. Per-row logprobs,
regenerated text, and per-step logits stay under gitignored analysis/.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
READOUTS_DIR = REPO_ROOT / "experiments" / "common" / "readouts"
if str(READOUTS_DIR) not in sys.path:
    sys.path.insert(0, str(READOUTS_DIR))

from path_compat import knowledge_probe_dir  # noqa: E402
from amendment_s_correctness_probe_score import (  # noqa: E402
    oof_probe,
    load_position_layers,
    paired_bootstrap_delta,
)
# Reuse the pure content-end helper unchanged so the answer-span boundary is
# computed identically to how the source rows' own `answer_tok_len` was.
from amendment_s_correctness_probe_extract import (  # noqa: E402
    _content_end_index,
    SYSTEM_PROMPT as S_SYSTEM_PROMPT,
)
from amendment_t_correctness_readout_deployment_extract import (  # noqa: E402
    SYSTEM_PROMPT as T_SYSTEM_PROMPT,
)

PROBE_DIR = knowledge_probe_dir()
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))
from backends import render_probe_prompt  # noqa: E402

CELL_YAML = HERE / "cell.yaml"
GATES_YAML = HERE / "gates.yaml"

# Reused BY IMPORT, never retyped (design draft sec.3.2): this is the render
# guarantee that makes regeneration a reproduction of the original generation
# rather than a new one.
ARM_SYSTEM_PROMPTS = {
    "s_base_primary": S_SYSTEM_PROMPT,
    "t_deployed_descriptive": T_SYSTEM_PROMPT,
}


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


@dataclass
class ArmConfig:
    id: str
    model_name: str
    adapter: str | None
    rows_path: Path
    tensors_dir: Path
    dial_layer: int
    dial_signed_auroc: float
    n_rows_expected: int
    gate: str
    system_prompt: str
    max_new_tokens: int
    do_sample: bool
    num_beams: int
    batch_size: int


def load_cell_config(cell_yaml_path: Path) -> dict:
    return yaml.safe_load(cell_yaml_path.read_text(encoding="utf-8"))


def load_gates_config(gates_yaml_path: Path) -> dict:
    return yaml.safe_load(gates_yaml_path.read_text(encoding="utf-8"))


def _gate_floor(gates_cfg: dict, gate_id: str) -> float:
    for g in gates_cfg["gates"]:
        if g["id"] == gate_id:
            return float(g["floor"])
    raise KeyError(f"gate {gate_id!r} not found in gates.yaml")


def _resolve_ref(raw: str | None, repo_root: Path) -> str | None:
    """A cell.yaml model/adapter field is either an HF hub id or a
    repo-relative local path (scratch/... for T). Resolve to an absolute
    local path if it exists on disk; otherwise pass the raw string through
    as a hub id (S's `unsloth/Qwen3-4B-bnb-4bit`)."""
    if raw is None:
        return None
    local = repo_root / raw
    return str(local) if local.exists() else raw


def arm_configs_from_cell(cell: dict, repo_root: Path) -> dict[str, ArmConfig]:
    gen = cell["generation"]
    out: dict[str, ArmConfig] = {}
    for arm in cell["arms"]:
        arm_id = arm["id"]
        out[arm_id] = ArmConfig(
            id=arm_id,
            model_name=arm["model"]["name"],
            adapter=arm["model"].get("adapter"),
            rows_path=repo_root / arm["rows"],
            tensors_dir=repo_root / arm["tensors_dir"],
            dial_layer=int(arm["dial_layer"]),
            dial_signed_auroc=float(arm["dial_signed_auroc"]),
            n_rows_expected=int(arm["n_rows_expected"]),
            gate=arm["gate"],
            system_prompt=ARM_SYSTEM_PROMPTS[arm_id],
            max_new_tokens=int(gen["max_new_tokens"]),
            do_sample=bool(gen["do_sample"]),
            num_beams=int(gen["num_beams"]),
            batch_size=int(gen["batch_size"]),
        )
    return out


# ---------------------------------------------------------------------------
# Row loading
# ---------------------------------------------------------------------------


def load_answered_rows(rows_path: Path) -> list[dict]:
    """Answered rows only (label in {correct, wrong}), matching the same
    filter `load_position_layers` applies to the cached tensors -- so the
    regeneration population and the dial-refit population are the same set."""
    rows: list[dict] = []
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("label") in ("correct", "wrong"):
                rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# Generation + capture (THE FIX)
# ---------------------------------------------------------------------------


def _eos_and_special_ids(tokenizer):
    """Replicates amendment_s/_t extractors' eos/special-id discovery inline
    (that logic is not factored into an importable function upstream); kept
    logic-identical so the generation stop condition matches the render the
    cached rows were produced under."""
    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end, int) and im_end >= 0:
        special_ids.add(im_end)
    eos_for_gen = tokenizer.eos_token_id
    if isinstance(im_end, int) and im_end >= 0:
        eos_for_gen = (
            [tokenizer.eos_token_id, im_end]
            if tokenizer.eos_token_id is not None
            else im_end
        )
    return eos_for_gen, special_ids


def regenerate_and_capture_row(
    model, tokenizer, device, row: dict, arm: ArmConfig, eos_for_gen, special_ids
) -> dict:
    """Regenerate ONE row's answer, capturing generation-time token IDs and
    per-step logits from the SAME model.generate() call (design draft
    sec.3.2). Never re-tokenizes decoded text -- this is the fix."""
    import torch
    import torch.nn.functional as F

    rendered, _mode = render_probe_prompt(
        tokenizer, arm.system_prompt, row["question"], enable_thinking=False
    )
    enc = tokenizer(rendered, return_tensors="pt").to(device)
    prompt_len = int(enc["input_ids"].shape[1])

    with torch.no_grad():
        gen = model.generate(
            **enc,
            max_new_tokens=arm.max_new_tokens,
            do_sample=arm.do_sample,
            num_beams=arm.num_beams,
            eos_token_id=eos_for_gen,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            return_dict_in_generate=True,
            output_scores=True,  # THE ADDITION over v1 / the S/T extractors
        )
    full_list = gen.sequences[0].tolist()
    new_ids = full_list[prompt_len:]  # generation-time IDs, cached HERE, never re-tokenized
    regenerated_answer_text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()

    # LP-G0 v2: exact by construction IFF this matches the cached text.
    roundtrip_ok = regenerated_answer_text == row["answer_text"]

    content_end = _content_end_index(full_list, prompt_len, special_ids)
    span_len = (content_end - prompt_len + 1) if content_end is not None else 0
    span_len = max(0, min(span_len, len(gen.scores)))

    step_logprobs: list[float] = []
    for step in range(span_len):
        logits = gen.scores[step][0]  # [vocab]
        logprobs = F.log_softmax(logits, dim=-1)
        token_id = new_ids[step]
        step_logprobs.append(float(logprobs[token_id].item()))

    variants = {
        "mean_answer_span": float(np.mean(step_logprobs)) if step_logprobs else float("nan"),
        "sum_answer_span": float(np.sum(step_logprobs)) if step_logprobs else float("nan"),
        "min_answer_span": float(np.min(step_logprobs)) if step_logprobs else float("nan"),
    }

    return {
        "row_key": row["row_key"],
        "roundtrip_ok": roundtrip_ok,
        "regenerated_answer_tok_len": span_len,
        "cached_answer_tok_len": row.get("answer_tok_len"),
        "variants": variants,
        "correct": row["correct"],
    }


def run_arm(
    model, tokenizer, device, arm: ArmConfig, rows: list[dict], runlog_path: Path
) -> list[dict]:
    """Regenerate+capture every answered row of one arm, with incremental,
    resumable persistence (append+flush per row; a kill mid-arm loses at most
    the in-flight row). Resuming skips row_keys already present in the log."""
    eos_for_gen, special_ids = _eos_and_special_ids(tokenizer)

    runlog_path.parent.mkdir(parents=True, exist_ok=True)
    done_keys: set[str] = set()
    if runlog_path.exists():
        with runlog_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    done_keys.add(json.loads(line)["row_key"])

    with runlog_path.open("a", encoding="utf-8") as out_fh:
        for row in rows:
            if row["row_key"] in done_keys:
                continue
            result = regenerate_and_capture_row(
                model, tokenizer, device, row, arm, eos_for_gen, special_ids
            )
            out_fh.write(json.dumps(result) + "\n")
            out_fh.flush()

    with runlog_path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ---------------------------------------------------------------------------
# Scoring (CPU-only; no model, no GPU)
# ---------------------------------------------------------------------------


def score_arm(
    arm: ArmConfig,
    per_row_results: list[dict],
    n_boot: int,
    seed: int,
    gates_cfg: dict,
    dial_reproduction_tolerance: float = 0.002,
) -> dict:
    """Dial refit (reused unchanged) + logprob AUROC + paired dial-minus-
    logprob margin. Reads the arm's EXISTING cached hidden-state tensors;
    needs no model."""
    X, y, keys = load_position_layers(arm.tensors_dir, "post")
    if arm.dial_layer not in X:
        raise RuntimeError(
            f"dial_layer {arm.dial_layer} not present in {arm.tensors_dir} "
            f"(layers on disk: {sorted(X)})"
        )
    X_dial = X[arm.dial_layer]
    p_dial = oof_probe(X_dial, y, seed)
    dial_refit_auroc = float(roc_auc_score(y, p_dial))
    dial_repro_ok = abs(dial_refit_auroc - arm.dial_signed_auroc) < dial_reproduction_tolerance

    by_key = {r["row_key"]: r for r in per_row_results}
    n_roundtrip_fail = sum(1 for r in per_row_results if not r["roundtrip_ok"])
    row_count_ok = len(per_row_results) == arm.n_rows_expected
    lp_g0_pass = dial_repro_ok and row_count_ok and (n_roundtrip_fail == 0)

    idx_common = [i for i, k in enumerate(keys) if k in by_key]
    y_common = y[idx_common]
    p_dial_common = p_dial[idx_common]

    variant_scores: dict[str, dict] = {}
    for variant in ("mean_answer_span", "sum_answer_span", "min_answer_span"):
        scores = np.array([by_key[keys[i]]["variants"][variant] for i in idx_common])
        variant_scores[variant] = {
            "auroc": float(roc_auc_score(y_common, scores)),
            "n": int(len(scores)),
        }

    primary = np.array([by_key[keys[i]]["variants"]["mean_answer_span"] for i in idx_common])
    dial_auroc_common = float(roc_auc_score(y_common, p_dial_common))
    primary_auroc = float(roc_auc_score(y_common, primary))
    margin = dial_auroc_common - primary_auroc
    margin_boot = paired_bootstrap_delta(y_common, p_dial_common, primary, n_boot, seed)

    gate_verdict: dict[str, Any]
    if not lp_g0_pass:
        gate_verdict = {"stopped_at_lp_g0": True}
    elif arm.gate == "LP-G1":
        floor = _gate_floor(gates_cfg, "LP-G1")
        lp_g1_pass = (margin >= floor) and (margin_boot["ci_lo"] > 0.0)
        falsifier_fired = (margin <= 0.0) and (margin_boot["ci_hi"] < 0.0)
        ambiguous = (not lp_g1_pass) and (not falsifier_fired)
        gate_verdict = {
            "LP_G1_pass": lp_g1_pass,
            "falsifier_fired": falsifier_fired,
            "ambiguous_band": ambiguous,
        }
    else:
        gate_verdict = {"descriptive_only": True}

    return {
        "arm": arm.id,
        "lp_g0": {
            "dial_repro_ok": dial_repro_ok,
            "dial_refit_auroc": round(dial_refit_auroc, 4),
            "dial_signed_auroc": arm.dial_signed_auroc,
            "row_count_ok": row_count_ok,
            "n_rows": len(per_row_results),
            "n_rows_expected": arm.n_rows_expected,
            "n_roundtrip_fail": n_roundtrip_fail,
            "pass": lp_g0_pass,
        },
        "variant_aurocs": variant_scores,
        "dial_minus_primary_logprob_margin": round(margin, 4),
        "margin_bootstrap_ci": margin_boot,
        "gate_verdict": gate_verdict,
    }


# ---------------------------------------------------------------------------
# Real model loading (GPU path; not exercised by the smoke, which injects a
# tiny CPU model/tokenizer directly into run_arm/score_arm instead)
# ---------------------------------------------------------------------------


def load_model_and_tokenizer(arm: ArmConfig):
    """Mirrors amendment_s/_t extractors' load code exactly (bfloat16,
    device_map=cuda, PEFT for the adapter arm) so regeneration runs under the
    same environment the original generation ran under."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_ref = _resolve_ref(arm.model_name, REPO_ROOT)
    adapter_ref = _resolve_ref(arm.adapter, REPO_ROOT)

    tokenizer = AutoTokenizer.from_pretrained(model_ref)
    base = AutoModelForCausalLM.from_pretrained(
        model_ref, torch_dtype=torch.bfloat16, device_map="cuda"
    )
    if adapter_ref is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(base, adapter_ref, adapter_name="v2_regen")
        model.set_adapter("v2_regen")
    else:
        model = base
    model.eval()
    device = next(model.parameters()).device
    return model, tokenizer, device


# ---------------------------------------------------------------------------
# --dry-run: real-input existence check, no model, no compute
# ---------------------------------------------------------------------------


def dry_run(cell: dict, repo_root: Path) -> int:
    """Resolve every real input named in cell.yaml; print the plan; load no
    model, compute nothing, write nothing. Returns 0 iff every input
    resolved, 2 iff any did not -- a correctly functioning existence check,
    not a crash indicator."""
    problems: list[str] = []
    plan: dict[str, Any] = {"arms": []}

    for arm_raw in cell["arms"]:
        arm_id = arm_raw["id"]
        rows_path = repo_root / arm_raw["rows"]
        tensors_dir = repo_root / arm_raw["tensors_dir"]
        arm_plan: dict[str, Any] = {
            "id": arm_id,
            "rows_path": str(rows_path),
            "tensors_dir": str(tensors_dir),
        }
        if not rows_path.exists():
            problems.append(f"{arm_id}: rows file not found: {rows_path}")
        else:
            with rows_path.open(encoding="utf-8") as fh:
                arm_plan["n_rows_on_disk"] = sum(1 for line in fh if line.strip())
        if not tensors_dir.is_dir():
            problems.append(f"{arm_id}: tensors_dir not found: {tensors_dir}")

        model_ref = _resolve_ref(arm_raw["model"]["name"], repo_root)
        arm_plan["model_ref"] = model_ref
        looks_local = (repo_root / arm_raw["model"]["name"]) == Path(model_ref)
        if looks_local and not Path(model_ref).exists():
            problems.append(f"{arm_id}: local model path not found: {model_ref}")

        raw_adapter = arm_raw["model"].get("adapter")
        if raw_adapter:
            adapter_ref = _resolve_ref(raw_adapter, repo_root)
            arm_plan["adapter_ref"] = adapter_ref
            if not Path(adapter_ref).exists():
                problems.append(f"{arm_id}: adapter not found: {adapter_ref}")

        plan["arms"].append(arm_plan)

    dial_module = READOUTS_DIR / "amendment_s_correctness_probe_score.py"
    plan["dial_refit_module"] = str(dial_module)
    if not dial_module.exists():
        problems.append(f"dial refit module not found: {dial_module}")

    print(json.dumps(plan, indent=2))
    if problems:
        print("\n[dry-run] UNRESOLVED real inputs:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
    print("\n[dry-run] all real inputs resolved.", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CELL_YAML)
    ap.add_argument("--gates", type=Path, default=GATES_YAML)
    ap.add_argument("--dry-run", action="store_true",
                     help="resolve real inputs and print the plan; exit 0/2, no compute")
    ap.add_argument("--arm", choices=sorted(ARM_SYSTEM_PROMPTS), default=None,
                     help="run this arm for real (GPU) -- requires the launch "
                          "precondition in AMENDMENT.md sec.8")
    ap.add_argument("--timing-smoke", type=int, default=None, metavar="N",
                     help="generation-only pass over the first N rows of --arm; "
                          "still GPU; NOT invoked by this build task")
    ap.add_argument("--seed", type=int, default=20260719)
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args(argv)

    cell = load_cell_config(a.config)

    if a.dry_run:
        return dry_run(cell, REPO_ROOT)

    if a.arm is None:
        print("nothing to do: pass --dry-run, or --arm <id> [--timing-smoke N]",
              file=sys.stderr)
        return 2

    arms = arm_configs_from_cell(cell, REPO_ROOT)
    arm = arms[a.arm]
    rows = load_answered_rows(arm.rows_path)
    if a.timing_smoke is not None:
        rows = rows[: a.timing_smoke]

    model, tokenizer, device = load_model_and_tokenizer(arm)
    runlog_path = HERE / "analysis" / arm.id / "runlog" / f"{arm.id}.jsonl"
    per_row = run_arm(model, tokenizer, device, arm, rows, runlog_path)

    if a.timing_smoke is not None:
        print(json.dumps({"arm": arm.id, "timing_smoke_n": len(per_row)}, indent=2))
        return 0

    gates_cfg = load_gates_config(a.gates)
    tol = gates_cfg["gates"][0].get("dial_reproduction_tolerance", 0.002)
    result = score_arm(arm, per_row, a.n_boot, a.seed, gates_cfg, tol)

    out_dir = HERE / "analysis-committed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"lp_v2_{arm.id}_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
