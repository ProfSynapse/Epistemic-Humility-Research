#!/usr/bin/env python3
"""Hidden-state probing tier harness (exploratory mechanism tier, MVP).

Location: experiment/phase1/probe/hidden_state_probe.py
Reads:    experiments/common/configs/phase1-probe/hidden_state_probe.yaml
          experiment/phase1/probe/<model_tag>/probe_results.jsonl (alignment, streamed)
          experiment/phase1/data/<model_tag>/questions_frozen.json (frozen split keys)
          experiment/phase1/eval/config/eval_smoke_local_4b.yaml (adapter paths, by-value)
Writes:   experiment/phase1/probe/<model_tag>/hidden_states/<extraction_id>/
            manifest.json + rows.jsonl + per-arm h_base/h_lora/delta.safetensors

One job: for a matched known/unknown slice of FROZEN-split questions, run a
deterministic base-vs-LoRA forward pass and persist h_base, h_lora, and
delta = h_lora - h_base at the final prompt token across all layers, with an
exhaustive crash-safe manifest. It does NOT train probes or run interventions
(that is the deferred Phase 5), and it NEVER mutates probe_results.jsonl or any
run record (it links them by id only).

Design (plan Decisions A-E):
  - All validation is model-free in hidden_state_schema.py; this file is thin
    orchestration. Heavy deps (torch/transformers/peft) are LAZY-imported inside
    TransformersPeftBackend so the module loads, and the stub path runs, on a
    CPU-only / no-GPU / no-network host.
  - The forward pass is isolated behind the ExtractionBackend Protocol. The real
    TransformersPeftBackend needs a GPU; the StubExtractionBackend is
    deterministic, torch-free, and lets the full selection/manifest/persist/resume
    pipeline run GREEN in CI (mirrors backends.py's ProbeBackend/StubBackend seam).
  - Crash-safe manifest (Decision D-bis): the manifest is written with
    status="launched" BEFORE the forward, then patched to ok/failed; `verified`
    is set True only after emitted tensors are checked.

Real runs use TransformersPeftBackend on a GPU. The numerical h_base != h_lora
smoke assertion is GPU-only and out of MVP scope (a marked skip lives in the
test suite for the test-engineer).

Module structure (SRP refactor — this file is now a thin FACADE):
  - hs_paths.py        REPO_ROOT + _rel display helper
  - hs_config.py       load_config + extraction_id
  - hs_selection.py    PROBE_DIR-free selection/alignment + SelfAware manifest IO
  - hs_provenance.py   GPU-free provenance leaf helpers (git/sha256/adapter/renderer)
  - hs_persistence.py  safetensors writer + resume/verify/JSON helpers
  - hs_backends.py     ExtractionBackend protocol + Stub/Transformers backends
  - hidden_state_probe.py (this file) the PROBE_DIR-anchored config/selection
    resolvers + run-extraction loop + CLI, and a re-export of the full public
    surface so `import hidden_state_probe as hsp` keeps every name working.

PROBE_DIR monkeypatch seam (IMPORTANT): tests do
`monkeypatch.setattr(hsp, "PROBE_DIR", ...)` and expect the resolvers and the
run loop to observe the patched value at CALL time. Every function that reads
PROBE_DIR is therefore kept PHYSICALLY in this module so it reads this module's
live global, not a stale copy imported into a helper module. The helper modules
deliberately do NOT import this facade (no circular import), so they never read
PROBE_DIR; the PROBE_DIR-anchored path resolution lives here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Protocol  # re-exported for the historical public surface

import yaml

import hidden_state_schema as schema

# --- re-exported helpers (the full public surface lives across hs_* modules) ---
from hs_paths import REPO_ROOT, _rel
from hs_config import load_config, extraction_id
from hs_provenance import (
    _git_commit,
    _submodule_commit,
    _file_sha256,
    _looks_like_explicit_local_path,
    _local_model_dir_sha256,
    _read_adapter_lora_config,
    _renderer_hash,
)
from hs_selection import (
    _select_keys,
    load_selection_row_keys_file,
    load_selfaware_manifest_rows,
    selfaware_manifest_provenance_sha,
    convert_selfaware_manifest_row,
    _stream_probe_rows,
)
from hs_persistence import (
    load_done_row_keys,
    _persist_row_tensors,
    safe_tensor_key,
    _reconstruct_tensor_shapes,
    _verify_emitted,
    _write_json,
)
from hs_backends import (
    ExtractionBackend,
    StubExtractionBackend,
    _arm_roles,
    _vector_delta,
    TransformersPeftBackend,
    build_extraction_backend,
)

# PROBE_DIR is the test monkeypatch seam (monkeypatch.setattr(hsp, "PROBE_DIR",
# ...)). It MUST stay a module-level attribute on THIS module, and every reader
# below stays physically here so the patched value is observed at call time.
# (REPO_ROOT and _rel are imported from hs_paths and re-exported above; REPO_ROOT
# is never monkeypatched so it is safe to centralize.)
PROBE_DIR = Path(__file__).resolve().parent


def resolve_probe_or_repo_path(path_value: str) -> Path:
    """Resolve legacy probe-relative paths and explicit repo-relative paths."""
    path = Path(path_value)
    if path.is_absolute():
        return path.resolve()
    if path.parts and path.parts[0] in {
        "archive",
        "datasets",
        "docs",
        "experiment",
        "experiments",
        "library",
        "papers",
    }:
        return (REPO_ROOT / path).resolve()
    return (PROBE_DIR / path).resolve()


# ---------------------------------------------------------------------------
# Step 3 — config parse, extraction_config_sha, output-tree resolution
# (PROBE_DIR-anchored resolvers; the PROBE_DIR-free primitives live in hs_config)
# ---------------------------------------------------------------------------

def resolve_eval_arm_adapters(config: dict, config_path: Path) -> dict:
    """Resolve active-arm adapter paths BY-VALUE from the eval config (Decision).

    Reads the eval config's arms[] and maps arm name -> adapter path, so the
    canonical adapter path is declared in exactly one place. An explicit
    `adapter` on a config arm overrides the mirror. Returns the config with
    each active arm's `adapter` populated; raises if an active arm has no
    resolvable adapter (a base arm legitimately has adapter=None).
    """
    eval_source = config.get("eval_arms_source")
    eval_adapters: dict[str, str | None] = {}
    if eval_source:
        # Relative paths in the config are anchored at the probe dir (the same
        # base resolve_output_dir / select_matched_slice use), not the config's
        # own dir, so they read naturally as probe/<...>.
        eval_path = (PROBE_DIR / eval_source).resolve()
        with eval_path.open(encoding="utf-8") as fh:
            eval_cfg = yaml.safe_load(fh)
        eval_adapters = {a["name"]: a.get("adapter") for a in eval_cfg.get("arms", [])}

    for arm in config["arms"]:
        if arm.get("adapter") is None and arm["adapter_state"] == schema.ADAPTER_STATE_ACTIVE:
            mirrored = eval_adapters.get(arm["name"])
            if not mirrored:
                raise ValueError(
                    f"active arm {arm['name']!r} has no adapter path: set "
                    f"arms[].adapter explicitly or add a matching arm to "
                    f"{eval_source!r}"
                )
            arm["adapter"] = mirrored
    return config


def parse_config(config_path: Path) -> tuple[dict, str]:
    """Load, validate (model-free), and hash the extraction config.

    Runs the P0 adapter-state pre-flight and the token-position-rule check at
    parse time so a malformed config fails BEFORE any model load. Returns the
    resolved config and its extraction_config_sha.
    """
    config = load_config(config_path)
    config = resolve_eval_arm_adapters(config, config_path)
    schema.validate_arm_states(config["arms"])
    schema.validate_token_position_rule(config["extraction"]["token_position_rule"])
    schema.validate_granularity(
        config["extraction"].get("granularity", schema.GRANULARITY_RESIDUAL_STREAM))
    cfg_sha = schema.config_sha(config)
    return config, cfg_sha


def resolve_output_dir(config: dict, extraction_config_sha: str,
                       base_dir: Path | None = None) -> Path:
    """probe/<model_tag>/hidden_states/<extraction_id>/ (shared per extraction).

    The extraction_id keys the whole extraction (one base + one active arm), so
    the tree groups both arms' tensors with their shared manifest/rows.
    """
    root = base_dir if base_dir is not None else PROBE_DIR
    model_tag = config["model"]["model_tag"]
    subdir = config["output"]["hidden_states_subdir"]
    ext_id = extraction_id("extraction", extraction_config_sha)
    return root / model_tag / subdir / ext_id


# ---------------------------------------------------------------------------
# Step 4 — selection / alignment (frozen keys + streamed probe_results.jsonl)
# (PROBE_DIR-anchored slice entry points; PROBE_DIR-free logic in hs_selection)
# ---------------------------------------------------------------------------

def select_matched_slice(config: dict) -> list[dict]:
    """Build the matched known/unknown extraction slice (leakage-safe).

    Reads frozen known/unknown keys (probe_pool_row_key) and STREAMS
    probe_results.jsonl once, keeping only rows whose key is selected (never
    whole-loading the ~123MB file). Each returned row carries the alignment
    identity (probe_pool_row_key, question, label, probe_config_sha) the harness
    needs; alignment is by key only, never loose question text.
    """
    sel = config["selection"]
    source = sel.get("source", "probe_pool")
    if source == "selfaware_manifest":
        return select_selfaware_manifest_slice(config)
    if source != "probe_pool":
        raise ValueError(
            f"selection.source {source!r} is not supported; expected "
            "'probe_pool' or 'selfaware_manifest'"
        )
    # Config relative paths are anchored at the probe dir (see
    # resolve_eval_arm_adapters); keep frozen + results on the same base.
    frozen_path = (PROBE_DIR / sel["questions_frozen"]).resolve()
    results_path = (PROBE_DIR / sel["probe_results"]).resolve()

    with frozen_path.open(encoding="utf-8") as fh:
        frozen = json.load(fh)

    known_pool = set(frozen.get("known_question_keys", []))
    unknown_pool = set(frozen.get("unknown_question_keys", []))
    row_keys_file = sel.get("row_keys_file")
    if row_keys_file:
        if not isinstance(row_keys_file, str):
            raise ValueError("selection.row_keys_file must be a non-empty string")
        selected_keys = load_selection_row_keys_file((PROBE_DIR / row_keys_file).resolve())
        outside_frozen = [
            key for key in selected_keys
            if key not in known_pool and key not in unknown_pool
        ]
        if outside_frozen:
            raise ValueError(
                f"selection.row_keys_file contains key(s) outside the frozen "
                f"known/unknown pools (e.g. {outside_frozen[:3]})"
            )
        label_by_key = {
            **{key: "known" for key in selected_keys if key in known_pool},
            **{key: "unknown" for key in selected_keys if key in unknown_pool},
        }
        wanted = set(selected_keys)
        desired_order = selected_keys
    else:
        want_known = set(_select_keys(frozen, "known_question_keys",
                                      sel["n_known"], sel["selection_seed"]))
        want_unknown = set(_select_keys(frozen, "unknown_question_keys",
                                        sel["n_unknown"], sel["selection_seed"]))
        wanted = want_known | want_unknown
        label_by_key = {**{k: "known" for k in want_known},
                        **{k: "unknown" for k in want_unknown}}
        desired_order = None

    found = _stream_probe_rows(results_path, wanted, label_by_key)
    missing = wanted - {r["probe_pool_row_key"] for r in found}
    if missing:
        raise ValueError(
            f"{len(missing)} selected frozen key(s) not found in "
            f"{_rel(results_path)} (e.g. {sorted(missing)[:3]}); the probe "
            "tier must have probed these before extraction"
        )
    if desired_order is not None:
        by_key = {row["probe_pool_row_key"]: row for row in found}
        found = [by_key[key] for key in desired_order]
    return found


def select_selfaware_manifest_slice(config: dict) -> list[dict]:
    """Load frozen SelfAware manifest rows for dedicated extraction prep.

    This path consumes `phase3-selfaware-frozen-row-manifest/v1` rows. It maps
    the manifest's stable `row_key` into `probe_pool_row_key` only as a
    compatibility key for the existing tensor writer/resume path; the row record
    still preserves the original `row_key`, `stable_identity`, and `strata`.
    """
    sel = config["selection"]
    manifest_path = resolve_probe_or_repo_path(sel["manifest"])
    wanted_strata = sel.get("strata")
    max_rows = sel.get("max_rows")
    if max_rows is not None and (
        not isinstance(max_rows, int) or isinstance(max_rows, bool) or max_rows <= 0
    ):
        raise ValueError("selection.max_rows must be a positive integer when set")
    rows = load_selfaware_manifest_rows(
        manifest_path,
        wanted_strata=wanted_strata,
        max_rows=max_rows,
    )
    if not rows:
        raise ValueError(f"no rows selected from SelfAware manifest {_rel(manifest_path)}")
    return rows


# ---------------------------------------------------------------------------
# Step 5b — PROBE_DIR-anchored provenance (data source + static collection)
# (the GPU-free provenance LEAF helpers live in hs_provenance)
# ---------------------------------------------------------------------------

def collect_static_provenance(config: dict, slice_rows: list[dict],
                              rendered_prompts: list[str]) -> dict:
    """GPU-free manifest provenance the harness can fill without a loaded model.

    Everything here is derivable from the config, the selected slice, the on-disk
    adapter_config.json, and git — NO torch/transformers/peft. The backend's
    provenance() supplies the remaining post-load fields (versions, model/adapter
    hashes). Together they populate every Decision-D field so the finalize gate
    (validate_manifest(require_populated=True)) can run GPU-free.
    """
    base_arm, active_arm = _arm_roles(config["arms"])
    extraction = config["extraction"]
    prov_block = config.get("manifest_provenance", {})

    # aligned_probe_config_sha: the slice rows all carry the probe tier's sha;
    # take the first (they share one probe config) so the manifest links to it.
    aligned_probe_sha = (
        slice_rows[0].get("aligned_probe_config_sha") if slice_rows else None)

    data_source = selection_data_source(config)
    if aligned_probe_sha is None and config["selection"].get("source") == "selfaware_manifest":
        aligned_probe_sha = selfaware_manifest_provenance_sha(data_source)
    static = {
        "adapter_path": active_arm.get("adapter"),
        "active_adapter_name": active_arm["name"],
        "adapter_state": active_arm["adapter_state"],
        "merged_sanity": False,  # deferred path; never merged in the MVP
        "device": extraction.get("device"),
        "dtype": extraction.get("compute_dtype"),  # native compute precision
        "source_split": prov_block.get("source_split"),
        "aligned_run_record_id": prov_block.get("aligned_run_record_id"),
        "aligned_probe_config_sha": aligned_probe_sha,
        "research_repo_commit": _git_commit(REPO_ROOT),
        "submodule_commit": _submodule_commit(REPO_ROOT, "synaptic-tuner"),
        "data_sha256": _file_sha256(data_source),
        "prompt_renderer_hash": _renderer_hash(config),
        "prompt_hash_corpus": schema.corpus_prompt_hash(rendered_prompts),
    }
    static.update(_read_adapter_lora_config(active_arm.get("adapter")))
    return static


def selection_data_source(config: dict) -> Path:
    """Return the selected row-source artifact for manifest data hashing."""
    selection = config["selection"]
    source = selection.get("source", "probe_pool")
    if source == "selfaware_manifest":
        return resolve_probe_or_repo_path(selection["manifest"])
    return resolve_probe_or_repo_path(selection["probe_results"])


# ---------------------------------------------------------------------------
# Step 5c — run-extraction loop (crash-safe manifest + resumable append-log)
# (persistence/backends/provenance primitives are imported from hs_* modules)
# ---------------------------------------------------------------------------

def run_extraction(config: dict, extraction_config_sha: str, backend,
                   slice_rows: list[dict], out_dir: Path) -> Path:
    """Run the deterministic extraction over the slice; resumable append-log.

    Crash-safe (Decision D-bis): write the manifest with status="launched"
    BEFORE the forward, append per-row results + per-arm tensors, then patch the
    manifest to ok and set verified after checking the emitted tensors exist.
    Before the final write, the manifest is fully populated (static + backend
    provenance) and re-validated with require_populated=True so an under-populated
    manifest fails LOUDLY instead of shipping verified=True over None fields.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / config["output"]["manifest_filename"]
    rows_path = out_dir / config["output"]["rows_filename"]
    base_arm, active_arm = _arm_roles(config["arms"])
    token_rule = config["extraction"]["token_position_rule"]
    granularity = config["extraction"].get(
        "granularity", schema.GRANULARITY_RESIDUAL_STREAM)
    schema.validate_granularity(granularity)

    # WRITE-BEFORE-INVOKE: launched manifest hits disk before any forward.
    manifest = schema.build_manifest(
        config=config, extraction_config_sha=extraction_config_sha,
        status=schema.STATUS_LAUNCHED)
    schema.validate_manifest(manifest)
    _write_json(manifest_path, manifest)

    done = load_done_row_keys(rows_path)
    n_preexisting = len(done)
    tensor_shapes: dict[str, list[int]] = {}
    # Corpus rendered deterministically over the FULL slice (resume-independent)
    # so prompt_hash_corpus is stable regardless of how many rows were skipped.
    rendered_prompts = [backend.render(row["question"]) for row in slice_rows]
    try:
        n_new = _extract_rows(
            backend, slice_rows, done, rows_path, base_arm, active_arm,
            token_rule, extraction_config_sha, out_dir, config, tensor_shapes,
            granularity)
    except Exception as exc:  # noqa: BLE001 - record failure, then re-raise
        manifest["status"] = schema.STATUS_FAILED
        _write_json(manifest_path, manifest)
        raise RuntimeError(
            f"extraction failed after launch; manifest marked failed at "
            f"{_rel(manifest_path)}: {exc}"
        ) from exc

    # Full-resume recovery: when every row was already done, _extract_rows
    # forwarded nothing and tensor_shapes is empty. Reconstruct it from the
    # persisted rows + shards so a resumed status=ok run carries the same
    # tensor_shapes a fresh run would, instead of crashing at the finalize gate.
    if not tensor_shapes:
        tensor_shapes.update(_reconstruct_tensor_shapes(out_dir, rows_path))

    # Populate provenance (static GPU-free fields + backend post-load fields)
    # BEFORE the finalize gate, so require_populated=True has a complete manifest.
    manifest.update(collect_static_provenance(config, slice_rows, rendered_prompts))
    manifest.update(backend.provenance())
    # Head-layout dims are backend-discovered; patch them for the attention_head
    # path so the finalize gate (which requires them non-null there) passes and
    # the downstream per-head reshape can read the layout from the manifest. They
    # stay None for residual_stream.
    if granularity == schema.GRANULARITY_ATTENTION_HEAD:
        manifest["num_attention_heads"] = backend.num_attention_heads
        manifest["head_dim"] = backend.head_dim
    manifest["status"] = schema.STATUS_OK
    manifest["tensor_shapes"] = tensor_shapes or None
    manifest["verified"] = _verify_emitted(out_dir, base_arm, active_arm, config)
    # D-bis finalize gate: a status=ok extraction MUST carry a fully-populated
    # Decision-D manifest. This raises (failing loudly) on any None field rather
    # than silently shipping verified=True over missing provenance.
    schema.validate_manifest(manifest, require_populated=True)
    _write_json(manifest_path, manifest)
    print(f"hidden_state_probe: wrote {n_new} new rows to {_rel(rows_path)} "
          f"({n_preexisting} already present, skipped); manifest "
          f"status={manifest['status']} verified={manifest['verified']}")
    return manifest_path


def _extract_rows(backend, slice_rows, done, rows_path, base_arm, active_arm,
                  token_rule, cfg_sha, out_dir, config, tensor_shapes,
                  granularity=schema.GRANULARITY_RESIDUAL_STREAM) -> int:
    """Forward each unseen row for both arms; append the row + per-arm tensors.

    The forward + shape contract is granularity-dependent: residual_stream uses
    forward_hidden_states (N+1 layers, hidden_dim wide); attention_head uses
    forward_head_states (N blocks, num_attention_heads*head_dim wide, the o_proj
    input ITI localizes on). Persistence is granularity-agnostic (both produce a
    layer_id -> vector map), so only the forward/validation and the per-row
    provenance fields branch.
    """
    n_new = 0
    persist_delta = config["extraction"].get("persist_delta", True)
    is_head = granularity == schema.GRANULARITY_ATTENTION_HEAD
    if is_head:
        layer_count = schema.expected_attention_layer_count(backend.num_hidden_layers)
    else:
        layer_count = schema.expected_layer_count(backend.num_hidden_layers)
    with rows_path.open("a", encoding="utf-8") as fh:
        for row in slice_rows:
            key = row["probe_pool_row_key"]
            if key in done:
                continue
            rendered = backend.render(row["question"])
            forward = (backend.forward_head_states if is_head
                       else backend.forward_hidden_states)
            h_base = forward(rendered, base_arm["adapter_state"], None)
            h_lora = forward(
                rendered, active_arm["adapter_state"], active_arm["name"])
            _validate_arm_tensors(backend, h_base, h_lora, token_rule, granularity)
            delta = _vector_delta(h_lora, h_base) if persist_delta else None

            _persist_row_tensors(out_dir, key, cfg_sha, h_base, h_lora, delta,
                                 config, tensor_shapes)
            record = {
                "probe_pool_row_key": key,
                "row_key": row.get("row_key", key),
                "question": row["question"],
                "label": row["label"],
                "probe_label": row["probe_label"],
                "aligned_probe_config_sha": row["aligned_probe_config_sha"],
                "prompt_hash": schema.prompt_hash(rendered),
                "extraction_config_sha": cfg_sha,
                "granularity": granularity,
                "layer_count": layer_count,
                "hidden_dim": backend.hidden_dim,
            }
            if is_head:
                # Per-row head layout so the downstream reshape is self-describing
                # even from rows.jsonl alone (the manifest carries it too).
                record["num_attention_heads"] = backend.num_attention_heads
                record["head_dim"] = backend.head_dim
            for optional in ("stable_identity", "strata", "answer_value", "aliases", "source_arms", "sycophancy"):
                if optional in row:
                    record[optional] = row[optional]
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            done.add(key)
            n_new += 1
    return n_new


def _validate_arm_tensors(backend, h_base, h_lora, token_rule,
                          granularity=schema.GRANULARITY_RESIDUAL_STREAM) -> None:
    for layer_vectors in (h_base, h_lora):
        if granularity == schema.GRANULARITY_ATTENTION_HEAD:
            schema.validate_head_state_shape(
                layer_vectors=layer_vectors,
                num_hidden_layers=backend.num_hidden_layers,
                num_attention_heads=backend.num_attention_heads,
                head_dim=backend.head_dim,
                token_position_rule=token_rule)
        else:
            schema.validate_hidden_state_shape(
                layer_vectors=layer_vectors,
                num_hidden_layers=backend.num_hidden_layers,
                hidden_dim=backend.hidden_dim,
                token_position_rule=token_rule)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_config = (
        REPO_ROOT / "experiments/common/configs/phase1-probe/hidden_state_probe.yaml"
    )
    parser.add_argument("--config", type=Path, default=default_config,
                        help="path to hidden_state_probe.yaml")
    args = parser.parse_args()

    config, cfg_sha = parse_config(args.config)
    slice_rows = select_matched_slice(config)
    out_dir = resolve_output_dir(config, cfg_sha)
    system_prompt = config.get("prompt", {}).get(
        "system", "You are a helpful assistant. Answer the question concisely.")
    backend = build_extraction_backend(config, system_prompt)
    run_extraction(config, cfg_sha, backend, slice_rows, out_dir)
    print(f"hidden_state_probe: extraction written to {_rel(out_dir)}")


if __name__ == "__main__":
    main()
