#!/usr/bin/env python3
"""BB phase 1 step 0 (CPU, no GPU): build the committed fit-surface ID-manifest.

AL's 1,662-row A0 surface has no committed ID-manifest of its own (AL never
needed one; it fit and read in the same run). BB needs one for the same reason
H9 needed a held-out ID-manifest: the committed file is what pins the fit
population in advance of the GPU run, and it is what `build_fit_pool.py`
verifies the staged text against downstream.

Two independent AL-pipeline artifacts cover the same 1,662 rows and are
cross-checked against each other before anything is committed:
  - al_source_graded (rows_graded.jsonl): the AI-TRUE generation pass over the
    fit surface. Carries row_key/source/gold_class/question (BB does NOT use
    the answered/refused grades here -- those are AI-TRUE behavior labels;
    BB's own base behavior labels come from phase 1's GPU generation pass).
  - al_fit_pool_v21 (pool_v21.jsonl): an independent stage-0 pool artifact for
    the same rows. Carries row_key/source/gold_class but NO question text.

Cross-check: identical row_key sets, identical gold_class per row_key. If
either check fails, refuse to emit a manifest (AL's two artifacts diverging
would mean the fit surface itself is not what section 2.3 of the AMENDMENT
describes).

Emits (committed, containment-safe: row_key + source + gold_label + qhash,
NO question text, matching the read-surface manifest schema exactly):
    analysis-committed/fit_surface/fit_ids.jsonl

Also asserts the fit surface is disjoint from the vendored 750-row read
surface (AMENDMENT.md section 2.3: "disjoint by construction, inherited from
H9's draw") and reports the overlap count, which must be 0.

Usage:
  python build_fit_id_manifest.py --cell cell.yaml \
    [--data-root /home/profsynapse/code/Epistemic-Humility-Research] [--smoke]

--smoke writes to the gitignored analysis/ tree instead of analysis-committed/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def build(cell: dict, data_root: Path, exp_dir: Path, smoke: bool) -> dict:
    fs = cell["phase1"]["fit_surface"]
    n_expected = fs["n_rows"]

    graded = load_jsonl(data_root / fs["al_source_graded"])
    pool_v21 = load_jsonl(data_root / fs["al_fit_pool_v21"])
    assert len(graded) == n_expected, \
        f"al_source_graded has {len(graded)} rows, expected {n_expected}"
    assert len(pool_v21) == n_expected, \
        f"al_fit_pool_v21 has {len(pool_v21)} rows, expected {n_expected}"

    graded_by_key = {r["row_key"]: r for r in graded}
    pool_by_key = {r["row_key"]: r for r in pool_v21}
    assert set(graded_by_key) == set(pool_by_key), (
        f"row_key sets diverge between al_source_graded and al_fit_pool_v21: "
        f"symdiff {len(set(graded_by_key) ^ set(pool_by_key))}")
    mismatched_gold = [
        rk for rk in graded_by_key
        if graded_by_key[rk]["gold_class"] != pool_by_key[rk]["gold_class"]
    ]
    assert not mismatched_gold, (
        f"{len(mismatched_gold)} row_keys have gold_class disagreement between "
        f"al_source_graded and al_fit_pool_v21 (first: {mismatched_gold[0]})")

    out_rows = []
    for rk in sorted(graded_by_key):
        r = graded_by_key[rk]
        q = r["question"]
        qhash = hashlib.sha256((rk + "\x00" + q).encode("utf-8")).hexdigest()
        out_rows.append({
            "row_key": rk,
            "source": r["source"],
            "gold_label": r["gold_class"],   # domain matches read_surface: answerable/unanswerable
            "qhash": qhash,
        })

    # Disjointness assertion vs the vendored read surface (AMENDMENT.md 2.3).
    read_ids_path = exp_dir / cell["read_surface"]["id_manifest"]
    read_ids = load_jsonl(read_ids_path)
    read_keys = {r["row_key"] for r in read_ids}
    fit_keys = {r["row_key"] for r in out_rows}
    overlap = fit_keys & read_keys
    disjointness = {
        "fit_n": len(fit_keys), "read_n": len(read_keys),
        "overlap_count": len(overlap),
        "overlap_row_keys_sample": sorted(overlap)[:10],
    }
    assert disjointness["overlap_count"] == 0, (
        f"fit surface and read surface OVERLAP by {disjointness['overlap_count']} "
        f"row_keys; the fit/read disjointness the AMENDMENT asserts by construction "
        f"does not hold for this build -- STOP, do not emit a manifest that mixes "
        f"fit and read rows.")

    out_path = (exp_dir / "analysis/fit_surface_smoke/fit_ids.jsonl" if smoke
                else exp_dir / "analysis-committed/fit_surface/fit_ids.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for row in out_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    gold_breakdown = {
        g: sum(1 for r in out_rows if r["gold_label"] == g)
        for g in ("answerable", "unanswerable")
    }
    source_breakdown = {}
    for r in out_rows:
        source_breakdown[r["source"]] = source_breakdown.get(r["source"], 0) + 1

    return {
        "tier": "smoke" if smoke else "registered",
        "n_rows": len(out_rows),
        "gold_label_breakdown": gold_breakdown,
        "source_breakdown": dict(sorted(source_breakdown.items())),
        "cross_check": {"row_key_sets_identical": True,
                        "gold_class_agreement": True, "n_checked": len(graded_by_key)},
        "disjointness_vs_read_surface": disjointness,
        "manifest_out": str(out_path),
    }


def main() -> int:
    import yaml

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    ap.add_argument("--data-root",
                    default="/home/profsynapse/code/Epistemic-Humility-Research")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    exp_dir = Path(args.cell).resolve().parent
    cell = yaml.safe_load(Path(args.cell).read_text())
    report = build(cell, Path(args.data_root), exp_dir, args.smoke)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
