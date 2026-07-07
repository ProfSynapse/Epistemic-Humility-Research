#!/usr/bin/env python3
"""Amendment AP - build the self-contained A0-surface pool for the Modal harness (CPU).

Pre-registered: experiments/ap-veto-length-balanced-confirmatory/AMENDMENT.md.
Confirmatory follow-up to Amendment AM (experiment/protocol/AMENDMENT-AM-residual-catch-veto-coverage.md).

AP screens the SAME frozen A0 question pool AM used (1662 rows, same
row_key/question/aliases/gold_class/category_canon join), not AM's 43-row
all-long residual: the hallucination-vs-good split is determined entirely by
the FRESH generation's own answered/refused/correct outcome at extract/grade
time, not by anything carried from this pool. score_L24 (AM's deterministic
residual-rule scalar) is deliberately DROPPED from the AP pool schema -- AP
has no residual rule and the veto must never see a pool scalar as a feature,
so leaving it out removes that leak vector by construction rather than by
promise.

Ported (logic, structure) from
experiment/phase1/probe/amendment_am_build_pool.py (read-only reference on the
unmerged amendment-am branch; not imported across branches). The join source
is the same AH stage0 host artifacts AM used:
  experiment/phase1/probe/analysis/ah_stage0/expansion/pool_v21.jsonl  (1662 rows)
  experiment/phase1/probe/analysis/ah_stage0/candidates.jsonl          (aliases)
  experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl

These are UNTRACKED / gitignored analysis artifacts (never contain FalseQA
text beyond the frozen A0 questions already in the pool; not committed). This
builder joins them into ONE self-contained pool file the Modal container
fetches from the private staging repo at launch time.

Each emitted row carries exactly what the container needs and nothing derived
on the GPU:
  row_key, safe_key, question, aliases, gold_class, category_canon
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE0 = REPO_ROOT / "experiment/phase1/probe/analysis/ah_stage0"
DEFAULT_POOL = STAGE0 / "expansion" / "pool_v21.jsonl"
CAND_FILES = [
    STAGE0 / "candidates.jsonl",
    STAGE0 / "expansion" / "expansion_candidates.jsonl",
]
DEFAULT_OUT = Path(__file__).resolve().parent / "analysis" / "ap_pool.jsonl"
EXPECTED_POOL = 1662


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def load_candidate_lookup():
    """row_key -> {question, aliases} joined from both candidate files (AH lineage)."""
    lut = {}
    for f in CAND_FILES:
        if not f.is_file():
            raise SystemExit(f"[ap/pool] missing candidate file {f}")
        for r in load_jsonl(f):
            lut[r["row_key"]] = {"question": r["question"],
                                 "aliases": r.get("aliases", [])}
    return lut


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", default=str(DEFAULT_POOL))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--skip-count-check", action="store_true")
    args = ap.parse_args(argv)

    pool_path = Path(args.pool).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pool = load_jsonl(pool_path)
    if not args.skip_count_check and len(pool) != EXPECTED_POOL:
        raise SystemExit(f"[ap/pool] pool has {len(pool)} rows, expected {EXPECTED_POOL}")
    lut = load_candidate_lookup()
    missing = [r["row_key"] for r in pool if r["row_key"] not in lut]
    if missing:
        raise SystemExit(f"[ap/pool] {len(missing)} rows missing question/aliases; "
                         f"first: {missing[:3]}")

    n_answerable = n_alias = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for r in pool:
            c = lut[r["row_key"]]
            gold_class = r["gold_class"]
            aliases = c["aliases"]
            if gold_class == "answerable":
                n_answerable += 1
                if aliases:
                    n_alias += 1
            fh.write(json.dumps({
                "row_key": r["row_key"],
                "safe_key": r["safe_key"],
                "question": c["question"],
                "aliases": aliases,
                "gold_class": gold_class,
                "category_canon": r.get("category_canon", ""),
                # score_L24 deliberately NOT carried (see module docstring).
            }, ensure_ascii=False) + "\n")

    print(f"[ap/pool] wrote {len(pool)} rows -> {out_path}", flush=True)
    print(f"[ap/pool] answerable={n_answerable} (with aliases={n_alias})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
