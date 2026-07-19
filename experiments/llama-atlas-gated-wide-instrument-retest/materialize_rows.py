#!/usr/bin/env python3
"""Materialize/join module for rr-cross-family-raw-refusal.

Joins, per family:
  1. The atlas's committed, ID-only role/split manifest
     (`jspace-family-atlas/analysis-committed/<cell_id>/split_manifest.json`)
     -- present in this repo, used as the authoritative row_key/role/split
     source and cross-checked against cell.yaml's registered heldout_power.
  2. The fleet's private row pool (question text + aliases), reused VERBATIM
     per AMENDMENT.md "Data reuse": `split_rows_private.jsonl` from
     `doubt-snap-cross-family-confirmatory`'s matching cell. This file is
     PRIVATE (gitignored everywhere in this repo) and is NOT committed to
     git; it must be staged locally before this script can render prompts or
     grade generations. See `--row-pool` and STAGED_INPUTS_NOTE below.
  3. The atlas's private full-depth anchor capture
     (`jspace-family-atlas/analysis/<cell_id>/atlas_capture/`, safetensors +
     `capture.jsonl` index, tensor keys `anchor__L{hidden_state_index}` --
     `synaptic-tuner/tuner/batch/engines/hf_batched.py:_capture_chunk`'s
     naming convention, confirmed by reading that module). This is ALSO
     PRIVATE and not committed; it must be staged (e.g. `modal volume get`
     from the atlas's capture run) before anchors can be extracted. Once
     staged, extraction itself (`extract_anchors_at_candidate_layers`) is a
     pure CPU slice over the already-captured tensors, not a GPU step: the
     atlas requested `--layers all`, so every candidate layer this cell
     needs is already sitting in the staged safetensors files. This module's
     success path writes the slice to `analysis/<family>/
     anchors_at_candidate_layers.json` (private, gitignored), the file
     `dose_ladder.py` and `heldout_scorer.py` both read anchors from.

Layer-index-convention resolution (cell.yaml's own open item, "pinned at sign
from the atlas's committed atlas_summary.json"): read in full before writing
this. atlas_summary.json's `per_layer` keys are 0..n_hidden_states-1, i.e.
the raw `output_hidden_states` tuple index (0 = embeddings, 1..N = decoder
block N's output) -- confirmed empirically: `per_layer["0"]` reads at exactly
0.5 AUROC (chance) on every axis in both families, the embedding-layer
signature, and `per_layer["20"]`/`per_layer["17"]` reproduce the AMENDMENT's
own cited raw_refusal points (llama 0.8967 at L20, mistral 0.925 at L17).
cell.yaml's `candidate_layers` are therefore stated in this SAME hs-index
convention (matching the atlas capture's own `anchor__L{N}` tensor key and
the ladder's hs20/hs23/hs26/hs30 naming), and the DECODER BLOCK to register a
write/read hook on is `hs_index - 1` (0-indexed), exactly
`fit_midband_directions.py`'s `_direction_record` comment and
`run_dose_ladder.py`'s `get_decoder_layer(model, hs_index - 1)`.

STAGED_INPUTS_NOTE: this CPU-only build could not verify anchor coverage
against real atlas captures because neither the fleet's private row pool nor
the atlas's private capture directory exist in this worktree (confirmed via
filesystem search before writing this module -- see NOTEBOOK.md). The
functions below are exercised by test_rr_smoke.py against synthetic
fixtures that mimic the real file layout exactly; running this script for
real requires staging both private inputs first at the paths this module
documents (or passing --row-pool / --atlas-capture-dir explicitly).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
ATLAS_DIR = REPO_ROOT / "experiments" / "jspace-family-atlas"
FLEET_DIR = REPO_ROOT / "experiments" / "doubt-snap-cross-family-confirmatory"

# THE CHANGE vs rr: single family only (cell.yaml `families`), per
# AMENDMENT.md "Motivation and posture" / harness-build instruction #1.
FAMILY_TO_CELL_ID = {
    "llama": "llama32_3b_instruct",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def family_cell(family: str) -> dict[str, Any]:
    cfg = load_yaml(HERE / "cell.yaml")
    for f in cfg["families"]:
        if f["id"] == FAMILY_TO_CELL_ID[family]:
            return f
    raise SystemExit(f"unknown family {family!r} (expected one of {sorted(FAMILY_TO_CELL_ID)})")


def resolve_revision(family: str) -> str:
    """cell.yaml's `families[].revision` field is a literal PLACEHOLDER
    string, not the real hash: the AMENDMENT says it is 'transcribed into
    cell.yaml from the fleet model_matrix.yaml at sign', but the version
    pinned (sha256-locked) at sign still carries the placeholder text
    unresolved. cell.yaml is locked and may not be edited to fix this (task
    binding rule), so this harness resolves the real revision live from the
    fleet's own model_matrix.yaml every run and never trusts cell.yaml's
    placeholder string -- see NOTEBOOK.md adjudication."""
    matrix = load_yaml(FLEET_DIR / "model_matrix.yaml")
    cell_id = FAMILY_TO_CELL_ID[family]
    for cell in matrix["cells"]:
        if cell["cell_id"] == cell_id:
            return cell["revision"]
    raise SystemExit(f"cell_id {cell_id!r} not found in {FLEET_DIR / 'model_matrix.yaml'}")


def load_split_manifest(family: str) -> list[dict[str, Any]]:
    """The atlas's committed, ID-only role/split manifest: present in this
    repo, no staging required."""
    cell_id = FAMILY_TO_CELL_ID[family]
    path = ATLAS_DIR / "analysis-committed" / cell_id / "split_manifest.json"
    if not path.is_file():
        raise SystemExit(f"missing committed atlas split_manifest.json: {path}")
    return load_json(path)["rows"]


def check_fit_population(family: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """THE CHANGE vs rr: this cell is FIT-only (AMENDMENT.md "Scope:
    FIT-side dose-ladder characterization"; cell.yaml has no `heldout_power`
    field at all, unlike rr's cell.yaml). This reports FIT/held-out
    population counts for provenance -- held_out rows are counted but NEVER
    read by dose_ladder.py -- and gates only on the FIT populations this
    cell actually consumes being non-empty, not on any held-out floor."""
    confab_fit = sum(1 for r in rows if r["role"] == "confab" and r.get("split") == "fit")
    known_fit = sum(1 for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "fit")
    unknown_refused = sum(1 for r in rows if r["role"] == "unknown_refused")
    confab_held = sum(1 for r in rows if r["role"] == "confab" and r.get("split") == "held_out")
    known_held = sum(1 for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "held_out")
    return {
        "confab_fit": confab_fit, "known_correct_answered_fit": known_fit, "unknown_refused_fit_only": unknown_refused,
        "confab_held_out_not_touched": confab_held, "known_correct_answered_held_out_not_touched": known_held,
        "floors_pass": confab_fit > 0 and known_fit > 0 and unknown_refused > 0,
    }


def join_row_text(split_rows: list[dict[str, Any]], row_pool_path: Path) -> list[dict[str, Any]]:
    """Join the atlas's ID-only split rows against the fleet's private row
    pool (question + aliases), keyed on row_key. Raises loudly (not a silent
    skip) if the private pool is missing or does not cover every ID row --
    this is a staging precondition, not a soft warning."""
    if not row_pool_path.is_file():
        raise SystemExit(
            f"row pool not found at {row_pool_path}. This is the fleet's "
            f"private split_rows_private.jsonl for this cell (question text "
            f"+ aliases), reused verbatim per AMENDMENT.md 'Data reuse'; it "
            f"is gitignored everywhere in this repo and must be staged "
            f"before materialization (e.g. pulled from the fleet's Modal "
            f"volume, mirroring qwen35-4b-midband-doubt-snap/"
            f"materialize_reused_rows.py's own download-then-verify pattern)."
        )
    pool = {r["row_key"]: r for r in load_jsonl(row_pool_path)}
    missing = [r["row_key"] for r in split_rows if r["row_key"] not in pool]
    if missing:
        raise SystemExit(
            f"{len(missing)} row_keys in the atlas split manifest are not "
            f"present in the staged row pool {row_pool_path}; sample: "
            f"{missing[:10]}"
        )
    joined = []
    for r in split_rows:
        p = pool[r["row_key"]]
        joined.append({
            **r,
            "question": p["question"],
            "aliases": p.get("aliases", []),
        })
    return joined


def anchor_tensor_key(candidate_layer: int) -> str:
    return f"anchor__L{candidate_layer}"


def decoder_block_index(candidate_layer_hs_index: int) -> int:
    """hs-index -> 0-indexed decoder block, per this module's own
    layer-index-convention resolution above."""
    return candidate_layer_hs_index - 1


def check_anchor_coverage(
    row_keys: list[str], candidate_layers: list[int], capture_index: list[dict[str, Any]],
) -> dict[str, Any]:
    """capture_index: the atlas capture's own `capture.jsonl` records
    (`{"id": row_key, "file": <safetensors filename>}`, one row per
    captured row -- the atlas requested `--layers all`, so a row present in
    this index carries every hidden-state layer, including every RR
    candidate layer, in its one safetensors file). Coverage is therefore a
    row-presence check, not a per-layer check, UNLESS a row's own
    safetensors file is missing the expected key (checked by the caller
    once tensors are actually loaded -- see `load_anchor_tensors`)."""
    captured_ids = {rec["id"] for rec in capture_index}
    missing = sorted(set(row_keys) - captured_ids)
    return {
        "n_rows_required": len(row_keys),
        "n_rows_captured": len(row_keys) - len(missing),
        "coverage_frac": (len(row_keys) - len(missing)) / max(1, len(row_keys)),
        "missing_row_keys_sample": missing[:20],
        "missing_row_count": len(missing),
        "candidate_layers_checked": candidate_layers,
        "pass": not missing,
        "recapture_rule": (
            "cell.yaml population.anchors.recapture_rule: if any row is "
            "missing, re-capture ONLY that layer's anchors under the atlas "
            "convention (GPU work, deferred -- this CPU-only build reports "
            "the gap and does not attempt a live recapture)."
        ),
    }


def load_anchor_tensors(
    row_keys: list[str], candidate_layers: list[int], capture_dir: Path,
) -> dict[str, dict[int, np.ndarray]]:
    """Returns {row_key: {candidate_layer: float64 vector}}. Raises if a
    captured row's safetensors file is missing an expected candidate-layer
    key -- a real per-layer gap distinct from the row-presence check above."""
    from safetensors.numpy import load_file

    index = load_jsonl(capture_dir / "capture.jsonl")
    by_id = {rec["id"]: rec for rec in index}
    out: dict[str, dict[int, np.ndarray]] = {}
    file_cache: dict[str, dict[str, np.ndarray]] = {}
    for rk in row_keys:
        rec = by_id.get(rk)
        if rec is None:
            raise SystemExit(f"row {rk!r} missing from capture index at {capture_dir}")
        fname = rec["file"]
        if fname not in file_cache:
            file_cache[fname] = load_file(str(capture_dir / fname))
        tensors = file_cache[fname]
        per_layer: dict[int, np.ndarray] = {}
        for layer in candidate_layers:
            key = anchor_tensor_key(layer)
            if key not in tensors:
                raise SystemExit(
                    f"row {rk!r}, layer {layer} (key {key!r}): tensor not "
                    f"found in {fname}. The atlas capture may not actually "
                    f"cover this candidate layer; per cell.yaml's "
                    f"recapture_rule this requires re-capturing that layer "
                    f"under the atlas convention (GPU work)."
                )
            per_layer[layer] = np.asarray(tensors[key], dtype=np.float64)
        out[rk] = per_layer
    return out


def extract_anchors_at_candidate_layers(
    row_keys: list[str], candidate_layers: list[int], capture_dir: Path,
) -> dict[str, dict[str, list[float]]]:
    """Slices the candidate-layer anchors out of the atlas's ALREADY-STAGED
    full-depth capture tensors, once staging has landed. This is a pure CPU
    operation over data the atlas already captured (`--layers all`, coverage
    1.00 per family per jspace-family-atlas/AMENDMENT.md:47-52); it is not
    the GPU recapture that `check_anchor_coverage`'s `recapture_rule` covers
    for a genuinely missing layer. Wraps `load_anchor_tensors` (which raises
    loudly, via SystemExit, on any row_key absent from the capture index or
    any candidate layer absent from a captured row's own tensors) and
    reshapes its output into the JSON-safe schema `dose_ladder.py` and
    `heldout_scorer.py` both read from `anchors_at_candidate_layers.json`:
    `{row_key: {str(layer): [float, ...]}}`."""
    per_row = load_anchor_tensors(row_keys, candidate_layers, capture_dir)
    return {
        rk: {str(layer): per_row[rk][layer].tolist() for layer in candidate_layers}
        for rk in row_keys
    }


def cmd_materialize(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if getattr(args, "out_dir", None) else HERE
    fcell = family_cell(args.family)
    revision = resolve_revision(args.family)
    if revision != fcell["revision"] and not fcell["revision"].startswith("PLACEHOLDER"):
        raise SystemExit(
            f"G0 revisions_byte_checked FAIL: resolved revision {revision!r} "
            f"does not match cell.yaml's pinned revision {fcell['revision']!r}"
        )

    split_rows = load_split_manifest(args.family)
    power = check_fit_population(args.family, split_rows)
    if not power["floors_pass"]:
        raise SystemExit(f"G0 fit_population_floors FAIL: {power}")

    row_pool_path = Path(args.row_pool) if args.row_pool else (
        HERE / "analysis" / "staged_inputs" / args.family / "split_rows_private.jsonl"
    )
    capture_dir = Path(args.atlas_capture_dir) if args.atlas_capture_dir else (
        ATLAS_DIR / "analysis" / FAMILY_TO_CELL_ID[args.family] / "atlas_capture"
    )

    result: dict[str, Any] = {
        "family": args.family,
        "cell_id": FAMILY_TO_CELL_ID[args.family],
        "model": fcell["model"],
        "revision": revision,
        "candidate_layers": fcell["candidate_layers"],
        "fit_population": power,
    }

    if not row_pool_path.is_file() or not (capture_dir / "capture.jsonl").is_file():
        result["staged_inputs_present"] = False
        result["note"] = (
            f"private staged inputs not found locally "
            f"(row_pool={row_pool_path} exists={row_pool_path.is_file()}; "
            f"atlas_capture_dir={capture_dir} exists={(capture_dir / 'capture.jsonl').is_file()}). "
            "Row-count/heldout-power checks above ran against the committed, "
            "ID-only atlas manifest and PASSED; anchor-coverage and row-text "
            "join require staging before this can run to completion. See "
            "this module's docstring."
        )
        pdir = out_dir / "analysis" / args.family
        write_json(pdir / "materialize_precondition_report.json", result)
        print(json.dumps(result, indent=2), flush=True)
        return

    result["staged_inputs_present"] = True
    joined = join_row_text(split_rows, row_pool_path)
    coverage = check_anchor_coverage(
        [r["row_key"] for r in joined], fcell["candidate_layers"],
        load_jsonl(capture_dir / "capture.jsonl"),
    )
    result["anchor_coverage"] = coverage
    if not coverage["pass"]:
        pdir = out_dir / "analysis" / args.family
        write_json(pdir / "materialize_report.json", result)
        raise SystemExit(f"G0 anchor_coverage FAIL: {coverage['missing_row_count']} rows missing")

    row_keys = [r["row_key"] for r in joined]
    anchors = extract_anchors_at_candidate_layers(row_keys, fcell["candidate_layers"], capture_dir)
    anchors_extracted = {
        "n_rows_extracted": len(anchors),
        "n_rows_joined": len(joined),
        "matches_joined_pool": len(anchors) == len(joined) and set(anchors) == set(row_keys),
        "candidate_layers": fcell["candidate_layers"],
    }
    result["anchors_extracted"] = anchors_extracted
    if not anchors_extracted["matches_joined_pool"]:
        pdir = out_dir / "analysis" / args.family
        write_json(pdir / "materialize_report.json", result)
        raise SystemExit(
            f"anchor extraction row count {len(anchors)} does not match the "
            f"joined pool ({len(joined)}); this should be unreachable given "
            f"load_anchor_tensors' own loud-raise semantics, so it flags a "
            f"real bug in this wiring, not a data gap."
        )

    pdir = out_dir / "analysis" / args.family
    write_jsonl(pdir / "joined_rows_private.jsonl", joined)
    write_json(pdir / "anchors_at_candidate_layers.json", anchors)
    write_json(pdir / "materialize_report.json", result)
    cdir = out_dir / "analysis-committed" / args.family
    write_json(cdir / "materialize_manifest.json", {
        "family": args.family, "cell_id": FAMILY_TO_CELL_ID[args.family],
        "model": fcell["model"], "revision": revision,
        "candidate_layers": fcell["candidate_layers"], "fit_population": power,
        "anchor_coverage": {k: v for k, v in coverage.items() if k != "missing_row_keys_sample"},
        "anchors_extracted": anchors_extracted,
        "rows": [
            {"row_key": r["row_key"], "role": r["role"], "split": r.get("split"),
             "source": r.get("source"), "category_canon": r.get("category_canon")}
            for r in joined
        ],
    })
    print(json.dumps(result, indent=2), flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", required=True, choices=sorted(FAMILY_TO_CELL_ID))
    ap.add_argument("--row-pool", default=None, help="path to the fleet's staged split_rows_private.jsonl")
    ap.add_argument("--atlas-capture-dir", default=None, help="path to the staged atlas_capture directory")
    ap.add_argument("--out-dir", default=None, help="override this experiment's root dir for analysis/ and analysis-committed/ writes (test hook)")
    ap.set_defaults(func=cmd_materialize)
    args = ap.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
