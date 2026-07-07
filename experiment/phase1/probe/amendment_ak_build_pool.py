#!/usr/bin/env python3
"""Amendment AK Stage 1 - build the commitment-point extraction pool (CPU-only).

Stage 1 reuses "the AH stage-0 question pool rows that produced the arm-B matched
set" (AMENDMENT-AK-commitment-point.md §3.1). Concretely that is the
unanswerable-clean A0 population from
`analysis/ah_main/gen_A0/rows.jsonl` (1,338 rows: gold_class == 'unanswerable',
not degenerate, not ungradeable) - the exact population the arm-B confab-signature
hunt (mi_confab_signature_20260704) and the M=328 matched design were built on.

This script emits one pool jsonl the GPU extraction runner consumes. Each line
carries only what the runner needs to render a prompt plus the CPU-side labels
the scorer needs to build strata (confab vs refuse) and the pilot split:

    row_key, question, label ("known"|"unknown"), gold_class,
    confab_on_unanswerable (bool), caution_dist_z (float),
    category_canon (str), source (str)

The full population is emitted; the CPU scorer applies the arm-B matched design
(within-flavor caliper match on caution_dist_z) and the 50-row pilot split from
this pool deterministically, so the pilot lock and the matched set are
reproducible from the pool alone.

NO-LICENSE note: the A0 rows already live in the local (gitignored) analysis
tree and some source text is FalseQA-adjacent. `question` is written to the pool
because the GPU runner needs it to render prompts; the pool is uploaded ONLY to
the PRIVATE staging dataset repo (never the public repo), matching the AI verdict
pool handling. Extraction outputs never write question text back (safe_key only).

CPU-only. No model, no GPU. Deterministic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
DEFAULT_A0 = (CANONICAL / "experiment/phase1/probe/analysis/ah_main/gen_A0/"
              "rows.jsonl")
DEFAULT_OUT = (CANONICAL / "experiment/phase1/probe/analysis/ak_stage1/"
               "ak_stage1_pool.jsonl")

# The arm-B population filter (mi_confab_signature_20260704 lines 75-77).
GOLD = "unanswerable"


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def build_pool(a0_rows: list[dict]) -> list[dict]:
    """Filter to the unanswerable-clean arm-B population and project fields.

    Order is preserved from the A0 rows.jsonl so the deterministic pilot split
    (first N rows after the scorer's own stable ordering) and the matched design
    reproduce byte-for-byte from this pool.
    """
    pool = []
    for r in a0_rows:
        if r.get("gold_class") != GOLD:
            continue
        if r.get("degenerate") or r.get("ungradeable"):
            continue
        label = "unknown"  # the whole population is unanswerable == unknown
        pool.append({
            "row_key": r["row_key"],
            "question": r["question"],
            "label": label,
            "gold_class": r["gold_class"],
            "confab_on_unanswerable": bool(r.get("confab_on_unanswerable")),
            "caution_dist_z": float(r.get("caution_dist_z")),
            "category_canon": r.get("category_canon", ""),
            "source": r.get("source", ""),
        })
    return pool


def summarize(pool: list[dict]) -> dict:
    n = len(pool)
    n_confab = sum(1 for r in pool if r["confab_on_unanswerable"])
    flavors: dict[str, int] = {}
    for r in pool:
        flavors[r["category_canon"]] = flavors.get(r["category_canon"], 0) + 1
    return {
        "n_total": n,
        "n_confab": n_confab,
        "n_refuse": n - n_confab,
        "per_flavor": dict(sorted(flavors.items())),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a0-rows", default=str(DEFAULT_A0),
                    help="arm-B A0 generation rows.jsonl (local, gitignored)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)

    a0_path = Path(args.a0_rows).resolve()
    if not a0_path.is_file():
        print(f"[ak/pool] FATAL: A0 rows not found: {a0_path}", file=sys.stderr)
        return 2
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    a0_rows = load_jsonl(a0_path)
    pool = build_pool(a0_rows)
    if not pool:
        print("[ak/pool] FATAL: empty pool after filtering", file=sys.stderr)
        return 2

    with out_path.open("w", encoding="utf-8") as fh:
        for item in pool:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    summ = summarize(pool)
    summ["a0_rows"] = str(a0_path)
    summ["n_a0_total"] = len(a0_rows)
    summ["out"] = str(out_path)
    (out_path.parent / "ak_stage1_pool_summary.json").write_text(
        json.dumps(summ, indent=2), encoding="utf-8")
    print(json.dumps(summ, indent=2), flush=True)
    print(f"[ak/pool] DONE {summ['n_total']} rows "
          f"({summ['n_confab']} confab / {summ['n_refuse']} refuse) -> {out_path}",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
