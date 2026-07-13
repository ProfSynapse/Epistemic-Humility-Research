#!/usr/bin/env python3
"""BB phase 1 (CPU, no GPU): registered near-duplicate sensitivity sweep
(AMENDMENT.md section 8), re-run over BB's fit/read population.

Produces the near_dup_flagged.json sidecar that score_bb_holdout.py
--sensitivity consumes. Token-overlap (Jaccard on whitespace tokens) between
each read-surface KUQ question and every fit-surface KUQ question; a
read-surface row whose MAX overlap against the fit surface is >= the pinned
threshold (cell.yaml sensitivity.near_dup_threshold) is flagged. The sidecar
carries row_keys ONLY (no text). Non-gating: score_bb_holdout.py recomputes
the reading AUROC with the flagged rows excluded and reports whether the
verdict flips, never pooling the two.

BECAUSE BB REUSES H9'S EXACT READ DRAW AND AL'S EXACT FIT SURFACE (AMENDMENT.md
section 2.3), the KUQ populations compared are identical to H9's own sweep,
which flagged 0 rows (max overlap 0.75) -- this script re-runs it for the
record rather than assuming that result carries over unchecked.

Question-text sources (both locally available in the canonical checkout, no
network needed):
  - read-surface KUQ text: the SAME local gitignored source JSONLs H9's own
    cell.yaml `holdout.complement_sources` declares (H9's committed draw was
    built from these files; BB's read surface IS that exact draw, so the same
    local files carry the same text) --
    experiment/phase1/probe/analysis/ah_stage0/pregen/rows.jsonl and
    experiment/phase1/probe/analysis/ah_stage0/expansion/score/scored_rows.jsonl.
  - fit-surface KUQ text: cell.yaml phase1.fit_surface.al_source_graded
    (rows_graded.jsonl), the same file build_fit_pool.py reads.

cell.yaml's `sensitivity` block (pinned) declares metric/threshold/kuq_sources/
flagged_out but not these text-source paths (H9's cell.yaml declared
`holdout.complement_sources` and `sensitivity.fit_surface_graded` for the
analogous role); this script hardcodes the two source paths above rather than
adding new keys to a pinned file. Flagged in the build report for the lead --
a future repin could promote these into cell.yaml if desired.

Usage:
  python near_dup_sweep_bb.py --cell cell.yaml \
    [--data-root /home/profsynapse/code/Epistemic-Humility-Research] [--smoke]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_TOK = re.compile(r"\w+")

# Local gitignored source paths (see module docstring for provenance).
READ_SURFACE_TEXT_SOURCES = (
    "experiment/phase1/probe/analysis/ah_stage0/pregen/rows.jsonl",
    "experiment/phase1/probe/analysis/ah_stage0/expansion/score/scored_rows.jsonl",
)


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def toks(q: str) -> set[str]:
    return set(_TOK.findall(q.lower()))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def sweep(cell: dict, data_root: Path, exp_dir: Path, smoke: bool) -> dict:
    sen = cell["sensitivity"]
    kuq = set(sen["kuq_sources"])
    thr = sen["near_dup_threshold"]

    read_ids = load_jsonl(exp_dir / cell["read_surface"]["id_manifest"])
    held_kuq_keys = {r["row_key"] for r in read_ids if r["source"] in kuq}

    held_text = {}
    for rel in READ_SURFACE_TEXT_SOURCES:
        for r in load_jsonl(data_root / rel):
            if r["row_key"] in held_kuq_keys:
                held_text[r["row_key"]] = r["question"]
    missing = held_kuq_keys - set(held_text)
    assert not missing, (
        f"{len(missing)} read-surface KUQ row_keys not found in the local "
        f"source JSONLs; the read surface may not actually be H9's exact "
        f"draw over these files.")

    fit_graded = load_jsonl(data_root / cell["phase1"]["fit_surface"]["al_source_graded"])
    fit_toks = [toks(r["question"]) for r in fit_graded if r["source"] in kuq]

    flagged = []
    max_overlaps = {}
    for rk, q in held_text.items():
        tq = toks(q)
        mx = max((jaccard(tq, ft) for ft in fit_toks), default=0.0)
        max_overlaps[rk] = mx
        if mx >= thr:
            flagged.append(rk)
    flagged.sort()

    out_path = (exp_dir / "analysis/near_dup_smoke/near_dup_flagged.json" if smoke
                else exp_dir / sen["flagged_out"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(flagged, indent=2))

    return {"tier": "smoke" if smoke else "registered",
            "metric": sen["near_dup_metric"], "threshold": thr,
            "n_held_kuq": len(held_kuq_keys), "n_fit_kuq": len(fit_toks),
            "n_flagged": len(flagged),
            "max_overlap_observed": max(max_overlaps.values(), default=0.0),
            "flagged_out": str(out_path)}


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
    print(json.dumps(sweep(cell, Path(args.data_root), exp_dir, args.smoke), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
