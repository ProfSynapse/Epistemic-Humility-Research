#!/usr/bin/env python3
"""Materialize/join module for rr2-mistral-adjudicated-refusal-confirm.

Single-family, single-layer adaptation of
`experiments/rr-cross-family-raw-refusal/materialize_rows.py` (read in full
before writing this): mistral7b_instruct_v03 only, candidate layer [16] only
(this experiment fixes one operating point, no sweep). Joins, per row:

  1. RR's own committed, ID-only role/split manifest, itself reused verbatim
     from the atlas
     (`experiments/jspace-family-atlas/analysis-committed/mistral7b_instruct_v03/
     split_manifest.json` -- present in this repo, no staging required).
  2. The fleet's private row pool (question text + aliases), reused VERBATIM
     per this experiment's cell.yaml `population.reuse_scope`. PRIVATE,
     gitignored everywhere in this repo, must be staged locally (identical
     staging precondition to RR's own materialize_rows.py -- same file,
     `<fleet>/split_rows_private.jsonl` for the mistral cell).
  3. The atlas's private full-depth anchor capture
     (`jspace-family-atlas/analysis/mistral7b_instruct_v03/atlas_capture/`),
     ALSO private and not committed, must be staged before anchors can be
     extracted. Once staged, extraction is a pure CPU slice (the atlas
     requested `--layers all`, so hs16 is already sitting in the staged
     safetensors files) -- identical mechanism to RR's own
     `extract_anchors_at_candidate_layers`, reused here unchanged apart from
     the single-layer scope.

Layer-index convention (hs_index -> decoder block = hs_index - 1) is
inherited from RR's own empirical resolution against the atlas's
`atlas_summary.json` (RR's materialize_rows.py docstring); not re-derived
here since it is a property of the atlas capture format, not per-experiment.
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

CELL_ID = "mistral7b_instruct_v03"


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


def family_cell() -> dict[str, Any]:
    cfg = load_yaml(HERE / "cell.yaml")
    return cfg["family"]


def candidate_layers() -> list[int]:
    cfg = load_yaml(HERE / "cell.yaml")
    return cfg["population"]["anchors"]["candidate_layers"]


def resolve_revision() -> str:
    """Live-reads the real revision from the fleet's own model_matrix.yaml,
    mirroring RR's own `resolve_revision` (RR's cell.yaml carried a
    PLACEHOLDER string through sign; this harness does not repeat that gap --
    cell.yaml's `family.revision` here is the real, lead-verified hash
    already, but this function still cross-checks it live rather than
    trusting the pinned file blindly, same discipline as RR)."""
    matrix = load_yaml(FLEET_DIR / "model_matrix.yaml")
    for cell in matrix["cells"]:
        if cell["cell_id"] == CELL_ID:
            return cell["revision"]
    raise SystemExit(f"cell_id {CELL_ID!r} not found in {FLEET_DIR / 'model_matrix.yaml'}")


def load_split_manifest() -> list[dict[str, Any]]:
    """The atlas's committed, ID-only role/split manifest: present in this
    repo, no staging required."""
    path = ATLAS_DIR / "analysis-committed" / CELL_ID / "split_manifest.json"
    if not path.is_file():
        raise SystemExit(f"missing committed atlas split_manifest.json: {path}")
    return load_json(path)["rows"]


def check_heldout_power(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fcell = family_cell()
    confab_held = sum(1 for r in rows if r["role"] == "confab" and r.get("split") == "held_out")
    known_held = sum(1 for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "held_out")
    expected = fcell["heldout_power"]
    return {
        "confab_held_out": confab_held,
        "known_correct_answered_held_out": known_held,
        "matches_cell_yaml": confab_held == expected["confab"] and known_held == expected["known_correct_answered"],
        "floors_pass": confab_held >= 150 and known_held >= 250,
        "cell_yaml_expected": expected,
    }


def join_row_text(split_rows: list[dict[str, Any]], row_pool_path: Path) -> list[dict[str, Any]]:
    """Join the atlas's ID-only split rows against the fleet's private row
    pool (question + aliases), keyed on row_key. Raises loudly (not a silent
    skip) if the private pool is missing or does not cover every ID row."""
    if not row_pool_path.is_file():
        raise SystemExit(
            f"row pool not found at {row_pool_path}. This is the fleet's "
            f"private split_rows_private.jsonl for the mistral cell (question "
            f"text + aliases), reused verbatim per cell.yaml 'population'; it "
            f"is gitignored everywhere in this repo and must be staged before "
            f"materialization, identical to RR's own staging precondition."
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
    """hs-index -> 0-indexed decoder block; identical convention to RR's own
    `materialize_rows.py:decoder_block_index` (property of the atlas capture
    format, not per-experiment)."""
    return candidate_layer_hs_index - 1


def check_anchor_coverage(
    row_keys: list[str], layers: list[int], capture_index: list[dict[str, Any]],
) -> dict[str, Any]:
    captured_ids = {rec["id"] for rec in capture_index}
    missing = sorted(set(row_keys) - captured_ids)
    return {
        "n_rows_required": len(row_keys),
        "n_rows_captured": len(row_keys) - len(missing),
        "coverage_frac": (len(row_keys) - len(missing)) / max(1, len(row_keys)),
        "missing_row_keys_sample": missing[:20],
        "missing_row_count": len(missing),
        "candidate_layers_checked": layers,
        "pass": not missing,
    }


def load_anchor_tensors(
    row_keys: list[str], layers: list[int], capture_dir: Path,
) -> dict[str, dict[int, np.ndarray]]:
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
        for layer in layers:
            key = anchor_tensor_key(layer)
            if key not in tensors:
                raise SystemExit(
                    f"row {rk!r}, layer {layer} (key {key!r}): tensor not "
                    f"found in {fname}."
                )
            per_layer[layer] = np.asarray(tensors[key], dtype=np.float64)
        out[rk] = per_layer
    return out


def extract_anchors_at_candidate_layers(
    row_keys: list[str], layers: list[int], capture_dir: Path,
) -> dict[str, dict[str, list[float]]]:
    per_row = load_anchor_tensors(row_keys, layers, capture_dir)
    return {
        rk: {str(layer): per_row[rk][layer].tolist() for layer in layers}
        for rk in row_keys
    }


def cmd_materialize(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if getattr(args, "out_dir", None) else HERE
    fcell = family_cell()
    layers = candidate_layers()
    revision = resolve_revision()
    if revision != fcell["revision"]:
        raise SystemExit(
            f"revision mismatch: fleet model_matrix.yaml resolves "
            f"{revision!r}, cell.yaml pins {fcell['revision']!r}"
        )

    split_rows = load_split_manifest()
    power = check_heldout_power(split_rows)
    if not power["matches_cell_yaml"] or not power["floors_pass"]:
        raise SystemExit(f"heldout_power_floors FAIL: {power}")

    row_pool_path = Path(args.row_pool) if args.row_pool else (
        HERE / "analysis" / "staged_inputs" / "split_rows_private.jsonl"
    )
    capture_dir = Path(args.atlas_capture_dir) if args.atlas_capture_dir else (
        ATLAS_DIR / "analysis" / CELL_ID / "atlas_capture"
    )

    result: dict[str, Any] = {
        "cell_id": CELL_ID, "model": fcell["model"], "revision": revision,
        "candidate_layers": layers, "heldout_power": power,
    }

    if not row_pool_path.is_file() or not (capture_dir / "capture.jsonl").is_file():
        result["staged_inputs_present"] = False
        result["note"] = (
            f"private staged inputs not found locally "
            f"(row_pool={row_pool_path} exists={row_pool_path.is_file()}; "
            f"atlas_capture_dir={capture_dir} exists={(capture_dir / 'capture.jsonl').is_file()}). "
            "Row-count/heldout-power checks above ran against the committed, "
            "ID-only atlas manifest and PASSED; anchor-coverage and row-text "
            "join require staging before this can run to completion."
        )
        pdir = out_dir / "analysis"
        write_json(pdir / "materialize_precondition_report.json", result)
        print(json.dumps(result, indent=2), flush=True)
        return

    result["staged_inputs_present"] = True
    joined = join_row_text(split_rows, row_pool_path)
    coverage = check_anchor_coverage(
        [r["row_key"] for r in joined], layers, load_jsonl(capture_dir / "capture.jsonl"),
    )
    result["anchor_coverage"] = coverage
    if not coverage["pass"]:
        pdir = out_dir / "analysis"
        write_json(pdir / "materialize_report.json", result)
        raise SystemExit(f"anchor_coverage FAIL: {coverage['missing_row_count']} rows missing")

    row_keys = [r["row_key"] for r in joined]
    anchors = extract_anchors_at_candidate_layers(row_keys, layers, capture_dir)
    anchors_extracted = {
        "n_rows_extracted": len(anchors),
        "n_rows_joined": len(joined),
        "matches_joined_pool": len(anchors) == len(joined) and set(anchors) == set(row_keys),
        "candidate_layers": layers,
    }
    result["anchors_extracted"] = anchors_extracted
    if not anchors_extracted["matches_joined_pool"]:
        pdir = out_dir / "analysis"
        write_json(pdir / "materialize_report.json", result)
        raise SystemExit(
            f"anchor extraction row count {len(anchors)} does not match the "
            f"joined pool ({len(joined)}); this should be unreachable given "
            f"load_anchor_tensors' own loud-raise semantics, so it flags a "
            f"real bug in this wiring, not a data gap."
        )

    pdir = out_dir / "analysis"
    write_jsonl(pdir / "joined_rows_private.jsonl", joined)
    write_json(pdir / "anchors_at_candidate_layers.json", anchors)
    write_json(pdir / "materialize_report.json", result)
    cdir = out_dir / "analysis-committed"
    write_json(cdir / "materialize_manifest.json", {
        "cell_id": CELL_ID, "model": fcell["model"], "revision": revision,
        "candidate_layers": layers, "heldout_power": power,
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
    ap.add_argument("--row-pool", default=None, help="path to the fleet's staged split_rows_private.jsonl")
    ap.add_argument("--atlas-capture-dir", default=None, help="path to the staged atlas_capture directory")
    ap.add_argument("--out-dir", default=None, help="override this experiment's root dir for analysis/ and analysis-committed/ writes (test hook)")
    ap.set_defaults(func=cmd_materialize)
    args = ap.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
