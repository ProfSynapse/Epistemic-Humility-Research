#!/usr/bin/env python3
"""H9 (CPU, no GPU): registered near-duplicate sensitivity sweep (C2).

Produces the near_dup_flagged.json sidecar that score_holdout --sensitivity
consumes (AMENDMENT.md section 8.1). Token-overlap (Jaccard on whitespace tokens)
between each held-out KUQ question and every fit-surface KUQ question; a held-out
row whose MAX overlap against the fit surface is >= the pinned threshold
(cell.yaml sensitivity.near_dup_threshold) is flagged. The sidecar carries
row_keys ONLY (no text). This is non-gating: it recomputes the reading AUROC with
the flagged rows excluded and reports whether the verdict flips.

Question text is read via --data-root (gitignored source JSONLs + AL's graded
rows) and never written out.

Usage:
  python near_dup_sweep.py --cell cell.yaml \
    [--data-root /home/profsynapse/code/Epistemic-Humility-Research] [--smoke]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_TOK = re.compile(r"\w+")


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
    ho = cell["holdout"]
    kuq = set(sen["kuq_sources"])
    thr = sen["near_dup_threshold"]

    ids_path = (exp_dir / "analysis/holdout_draw_smoke/holdout_ids.jsonl" if smoke
                else exp_dir / ho["id_manifest_out"])
    ids = load_jsonl(ids_path)
    held_kuq_keys = {r["row_key"] for r in ids if r["source"] in kuq}

    # held-out KUQ question text from the source JSONLs
    held_text = {}
    for rel in (ho["complement_sources"]["orig_rows"],
                ho["complement_sources"]["expansion_rows"]):
        for r in load_jsonl(data_root / rel):
            if r["row_key"] in held_kuq_keys:
                held_text[r["row_key"]] = r["question"]

    # fit-surface KUQ question text from AL's graded rows
    fit_toks = [toks(r["question"]) for r in load_jsonl(data_root / sen["fit_surface_graded"])
                if r["source"] in kuq]

    flagged = []
    max_overlaps = {}
    for rk, q in held_text.items():
        tq = toks(q)
        mx = max((jaccard(tq, ft) for ft in fit_toks), default=0.0)
        max_overlaps[rk] = mx
        if mx >= thr:
            flagged.append(rk)
    flagged.sort()

    out_path = (exp_dir / "analysis/holdout_draw_smoke/near_dup_flagged.json" if smoke
                else exp_dir / sen["flagged_out"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(flagged, indent=2))

    return {"tier": "smoke" if smoke else "registered",
            "metric": sen["near_dup_metric"], "threshold": thr,
            "n_held_kuq": len(held_kuq_keys), "n_flagged": len(flagged),
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
