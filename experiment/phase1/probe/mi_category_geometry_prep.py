#!/usr/bin/env python3
"""Prep for the Tier-1 category-geometry MI fleet (backlog item 22).

Builds a shared analysis surface from the Amendment AH stage-0 + expansion
pregen extractions (raw Qwen3-4B instruct base, anchor position, L0-L36,
2560 dims) so downstream analyses load per-layer matrices instead of
re-reading 18.5k per-row safetensors.

Outputs (untracked, analysis/mi_category_geometry_20260704/cache/):
  manifest.jsonl  one row per cached item, in cache row order:
                  row_key, label (known/unknown), source,
                  category_canon ('' if uncategorized), split (stage0/expansion)
  L{i}.npy        float16 [n_rows, 2560] aligned to manifest order, i = 0..36

Row selection: ALL unknown rows (categorized or not) + a fixed-seed sample of
6000 known rows (stratified by source). Exploratory lab-notebook tier.
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
AH = REPO / "experiment/phase1/probe/analysis/ah_stage0"
OUT = REPO / "experiment/phase1/probe/analysis/mi_category_geometry_20260704/cache"
SEED = 20260704
N_KNOWN = 6000
N_LAYERS = 37

CANON = {
    "underspecified question": "ambiguous",
    "ambiguous": "ambiguous",
    "future unknown": "future_unknown",
    "controversial/debatable question": "controversial",
    "controversial": "controversial",
    "false assumption": "false_assumption",
    "question with false assumption": "false_assumption",
    "unsolved problem/mistery": "unsolved_problem",
    "unsolved problem": "unsolved_problem",
    "counterfactual questions": "counterfactual",
    "counterfactual": "counterfactual",
}


def canon(raw):
    return CANON.get((raw or "").strip().lower(), "")


def load_rows():
    backfill = {}
    with open(AH / "expansion/mined_kuq_category_backfill.jsonl") as f:
        for line in f:
            r = json.loads(line)
            backfill[r["row_key"]] = r.get("category", "")

    rows = []
    with open(AH / "candidates.jsonl") as f:
        for line in f:
            r = json.loads(line)
            safe = r["row_key"].replace("::", "__")
            rows.append(
                {
                    "row_key": r["row_key"],
                    "label": r["label"],
                    "source": r["source"],
                    "category_canon": canon(backfill.get(r["row_key"], "")),
                    "split": "stage0",
                    "path": str(AH / "pregen" / f"{safe}__pre.safetensors"),
                }
            )
    with open(AH / "expansion/expansion_candidates.jsonl") as f:
        for line in f:
            r = json.loads(line)
            safe = r["row_key"].replace("::", "__")
            rows.append(
                {
                    "row_key": r["row_key"],
                    "label": r["label"],
                    "source": r["source"],
                    "category_canon": canon(r.get("category", "")),
                    "split": "expansion",
                    "path": str(AH / "expansion/pregen" / f"{safe}__pre.safetensors"),
                }
            )
    return rows


def select(rows):
    unknowns = [r for r in rows if r["label"] == "unknown"]
    knowns = [r for r in rows if r["label"] == "known"]
    rng = np.random.default_rng(SEED)
    by_source = defaultdict(list)
    for r in knowns:
        by_source[r["source"]].append(r)
    picked = []
    frac = N_KNOWN / len(knowns)
    for src, pool in sorted(by_source.items()):
        k = max(1, round(frac * len(pool)))
        idx = rng.choice(len(pool), size=min(k, len(pool)), replace=False)
        picked.extend(pool[i] for i in idx)
    return unknowns + picked


def main():
    from safetensors.numpy import load_file

    rows = select(load_rows())
    print(f"selected {len(rows)} rows "
          f"({sum(r['label'] == 'unknown' for r in rows)} unknown, "
          f"{sum(bool(r['category_canon']) for r in rows)} categorized)")

    OUT.mkdir(parents=True, exist_ok=True)
    kept, missing = [], 0
    mats = [np.empty((len(rows), 2560), dtype=np.float16) for _ in range(N_LAYERS)]
    for r in rows:
        p = Path(r["path"])
        if not p.exists():
            missing += 1
            continue
        t = load_file(str(p))
        i = len(kept)
        for li in range(N_LAYERS):
            mats[li][i] = t[f"L{li}"].reshape(-1).astype(np.float16)
        kept.append(r)
        if len(kept) % 2000 == 0:
            print(f"  loaded {len(kept)}", flush=True)
    if missing:
        print(f"WARN: {missing} rows had no tensor file")

    n = len(kept)
    with open(OUT / "manifest.jsonl", "w") as f:
        for r in kept:
            f.write(json.dumps({k: r[k] for k in
                                ("row_key", "label", "source",
                                 "category_canon", "split")}) + "\n")
    for li in range(N_LAYERS):
        np.save(OUT / f"L{li}.npy", mats[li][:n])
    print(f"wrote {n} rows x {N_LAYERS} layers to {OUT}")


if __name__ == "__main__":
    main()
