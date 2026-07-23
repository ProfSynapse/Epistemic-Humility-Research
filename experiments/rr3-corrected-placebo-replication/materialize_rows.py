#!/usr/bin/env python3
"""Materialize/join module for rr3-corrected-placebo-replication.

Two-family generalization of
`experiments/rr2-mistral-adjudicated-refusal-confirm/materialize_rows.py`
(single-family, mistral-only), read in full before writing this, following
the multi-family PATTERN of `experiments/rr-cross-family-raw-refusal/
materialize_rows.py` (also read in full): one candidate layer per family (16
mistral, 20 llama; this experiment fixes both operating points, no sweep),
`--family {mistral,llama}`.

Per cell.yaml `population.reuse_from`, RR3 reuses the population RR's own
mistral and llama cells used verbatim -- which is, mechanically, the SAME two
files RR2 already established the staging contract for: the atlas's
committed, ID-only role/split manifest
(`experiments/jspace-family-atlas/analysis-committed/<cell_id>/
split_manifest.json`, present in this repo, no staging required) joined
against the fleet's private row pool (question text + aliases,
`doubt-snap-cross-family-confirmatory/analysis/staged_inputs/<family>/
split_rows_private.jsonl`, PRIVATE, gitignored, must be staged locally) and
the atlas's private full-depth anchor capture (`jspace-family-atlas/analysis/
<cell_id>/atlas_capture/`, ALSO private, must be staged; once staged,
extraction is a pure CPU slice since the atlas requested `--layers all`).

Joining ALL split rows (not just `held_out`) is deliberate and load-bearing
for two downstream needs: `fit_reuse.py` reconstructs each family's frozen
fit from the `fit`-split confab/known-correct rows plus the `unknown_refused`
(`fit_only`) rows (mirrors RR2's `fit_reuse.py`), and the held-back
clear-negative decoy pool (`heldout_scorer.py:run_heldback_decoy_pass`,
AMENDMENT.md "Successor instrument fix (a)") is generated from the
`known_correct_answered` rows at `split == "fit"` -- rows that are NEVER part
of any held-out scored arm, so decoys drawn from them cannot cannibalize
scored cost coverage the way carving decoys out of the SCORED known-correct
population would (the calibration's fix (a) failure mode this experiment is
required to close).
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

FAMILY_TO_CELL_ID = {
    "mistral": "mistral7b_instruct_v03",
    "llama": "llama32_3b_instruct",
}
FAMILY_TO_LAYER = {
    "mistral": 16,
    "llama": 20,
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


def load_cell_yaml() -> dict[str, Any]:
    return load_yaml(HERE / "cell.yaml")


def family_block(family: str) -> dict[str, Any]:
    """Returns the {model, revision, heldout_power, ...} block for `family`:
    core_cell.family for mistral, the rider_llama_placebo_ladder entry for
    llama (cell.yaml's two families live in different sub-trees since only
    mistral has a promotion-gated core cell)."""
    cell = load_cell_yaml()
    if family == "mistral":
        return cell["core_cell"]["family"]
    if family == "llama":
        rider = next(r for r in cell["rider_cells"] if isinstance(r, dict) and r.get("id") == "rider_llama_placebo_ladder")
        return {
            "id": rider["family"], "model": rider["model"], "revision": rider["revision"],
            "substrate": rider["substrate"], "loader": rider["loader"],
            "n_decoder_layers": 28, "atlas_hidden_states": 29,
            "heldout_power": rider["heldout_power"],
        }
    raise SystemExit(f"unknown family {family!r} (expected 'mistral' or 'llama')")


def candidate_layer(family: str) -> int:
    return FAMILY_TO_LAYER[family]


def resolve_revision(family: str) -> str:
    """Live-reads the real revision from the fleet's own model_matrix.yaml,
    mirroring RR2's `resolve_revision` discipline (cross-check the pinned
    cell.yaml value against the live source, hard stop on mismatch, never
    trust the pin blindly)."""
    matrix = load_yaml(FLEET_DIR / "model_matrix.yaml")
    cell_id = FAMILY_TO_CELL_ID[family]
    for cell in matrix["cells"]:
        if cell["cell_id"] == cell_id:
            return cell["revision"]
    raise SystemExit(f"cell_id {cell_id!r} not found in {FLEET_DIR / 'model_matrix.yaml'}")


def load_split_manifest(family: str) -> list[dict[str, Any]]:
    """The atlas's committed, ID-only role/split manifest: present in this
    repo, no staging required. Returns EVERY row (fit, fit_only, held_out
    splits alike) -- fit_reuse.py and the held-back decoy pass both need
    fit-split rows this materialize step must not filter out."""
    cell_id = FAMILY_TO_CELL_ID[family]
    path = ATLAS_DIR / "analysis-committed" / cell_id / "split_manifest.json"
    if not path.is_file():
        raise SystemExit(f"missing committed atlas split_manifest.json: {path}")
    return load_json(path)["rows"]


def check_heldout_power(family: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    fcell = family_block(family)
    confab_held = sum(1 for r in rows if r["role"] == "confab" and r.get("split") == "held_out")
    known_held = sum(1 for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "held_out")
    known_fit = sum(1 for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "fit")
    expected = fcell["heldout_power"]
    return {
        "confab_held_out": confab_held,
        "known_correct_answered_held_out": known_held,
        "known_correct_answered_fit": known_fit,
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
            f"private split_rows_private.jsonl for this family (question "
            f"text + aliases), reused verbatim per cell.yaml 'population'; it "
            f"is gitignored everywhere in this repo and must be staged before "
            f"materialization, identical to RR/RR2's own staging precondition."
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


def anchor_tensor_key(candidate_layer_hs: int) -> str:
    return f"anchor__L{candidate_layer_hs}"


def decoder_block_index(candidate_layer_hs_index: int) -> int:
    """hs-index -> 0-indexed decoder block; identical convention to RR/RR2's
    own `decoder_block_index` (property of the atlas capture format, not
    per-experiment)."""
    return candidate_layer_hs_index - 1


def check_anchor_coverage(
    row_keys: list[str], layer: int, capture_index: list[dict[str, Any]],
) -> dict[str, Any]:
    captured_ids = {rec["id"] for rec in capture_index}
    missing = sorted(set(row_keys) - captured_ids)
    return {
        "n_rows_required": len(row_keys),
        "n_rows_captured": len(row_keys) - len(missing),
        "coverage_frac": (len(row_keys) - len(missing)) / max(1, len(row_keys)),
        "missing_row_keys_sample": missing[:20],
        "missing_row_count": len(missing),
        "candidate_layer_checked": layer,
        "pass": not missing,
    }


def load_anchor_tensors(
    row_keys: list[str], layer: int, capture_dir: Path,
) -> dict[str, np.ndarray]:
    from safetensors.numpy import load_file

    index = load_jsonl(capture_dir / "capture.jsonl")
    by_id = {rec["id"]: rec for rec in index}
    out: dict[str, np.ndarray] = {}
    file_cache: dict[str, dict[str, np.ndarray]] = {}
    key = anchor_tensor_key(layer)
    for rk in row_keys:
        rec = by_id.get(rk)
        if rec is None:
            raise SystemExit(f"row {rk!r} missing from capture index at {capture_dir}")
        fname = rec["file"]
        if fname not in file_cache:
            file_cache[fname] = load_file(str(capture_dir / fname))
        tensors = file_cache[fname]
        if key not in tensors:
            raise SystemExit(f"row {rk!r}, layer {layer} (key {key!r}): tensor not found in {fname}.")
        out[rk] = np.asarray(tensors[key], dtype=np.float64)
    return out


def extract_anchors_at_layer(row_keys: list[str], layer: int, capture_dir: Path) -> dict[str, dict[str, list[float]]]:
    per_row = load_anchor_tensors(row_keys, layer, capture_dir)
    return {rk: {str(layer): per_row[rk].tolist()} for rk in row_keys}


def cmd_materialize(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir) if getattr(args, "out_dir", None) else HERE
    family = args.family
    fcell = family_block(family)
    layer = candidate_layer(family)
    revision = resolve_revision(family)
    if revision != fcell["revision"]:
        raise SystemExit(
            f"revision mismatch for family={family!r}: fleet model_matrix.yaml "
            f"resolves {revision!r}, cell.yaml pins {fcell['revision']!r}"
        )

    split_rows = load_split_manifest(family)
    power = check_heldout_power(family, split_rows)
    if not power["matches_cell_yaml"] or not power["floors_pass"]:
        raise SystemExit(f"heldout_power_floors FAIL ({family}): {power}")

    row_pool_path = Path(args.row_pool) if args.row_pool else (
        HERE / "analysis" / "staged_inputs" / family / "split_rows_private.jsonl"
    )
    capture_dir = Path(args.atlas_capture_dir) if args.atlas_capture_dir else (
        ATLAS_DIR / "analysis" / FAMILY_TO_CELL_ID[family] / "atlas_capture"
    )

    result: dict[str, Any] = {
        "family": family, "cell_id": FAMILY_TO_CELL_ID[family],
        "model": fcell["model"], "revision": revision,
        "candidate_layer": layer, "heldout_power": power,
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
        pdir = out_dir / "analysis" / family
        write_json(pdir / "materialize_precondition_report.json", result)
        print(json.dumps(result, indent=2), flush=True)
        return

    result["staged_inputs_present"] = True
    joined = join_row_text(split_rows, row_pool_path)
    coverage = check_anchor_coverage(
        [r["row_key"] for r in joined], layer, load_jsonl(capture_dir / "capture.jsonl"),
    )
    result["anchor_coverage"] = coverage
    if not coverage["pass"]:
        pdir = out_dir / "analysis" / family
        write_json(pdir / "materialize_report.json", result)
        raise SystemExit(f"anchor_coverage FAIL ({family}): {coverage['missing_row_count']} rows missing")

    row_keys = [r["row_key"] for r in joined]
    anchors = extract_anchors_at_layer(row_keys, layer, capture_dir)
    anchors_extracted = {
        "n_rows_extracted": len(anchors),
        "n_rows_joined": len(joined),
        "matches_joined_pool": len(anchors) == len(joined) and set(anchors) == set(row_keys),
        "candidate_layer": layer,
    }
    result["anchors_extracted"] = anchors_extracted
    if not anchors_extracted["matches_joined_pool"]:
        pdir = out_dir / "analysis" / family
        write_json(pdir / "materialize_report.json", result)
        raise SystemExit(
            f"anchor extraction row count {len(anchors)} does not match the "
            f"joined pool ({len(joined)}) for family={family!r}; this should "
            f"be unreachable given load_anchor_tensors' own loud-raise "
            f"semantics, so it flags a real bug in this wiring, not a data gap."
        )

    pdir = out_dir / "analysis" / family
    write_jsonl(pdir / "joined_rows_private.jsonl", joined)
    write_json(pdir / "anchors_at_candidate_layer.json", anchors)
    write_json(pdir / "materialize_report.json", result)
    cdir = out_dir / "analysis-committed" / family
    write_json(cdir / "materialize_manifest.json", {
        "family": family, "cell_id": FAMILY_TO_CELL_ID[family],
        "model": fcell["model"], "revision": revision,
        "candidate_layer": layer, "heldout_power": power,
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
