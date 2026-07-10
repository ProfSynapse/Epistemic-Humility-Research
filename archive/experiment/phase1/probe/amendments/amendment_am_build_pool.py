#!/usr/bin/env python3
"""Amendment AM - build the self-contained A0-surface pool for the Modal harness (CPU).

Pre-registered: experiments/residual-catch-veto-coverage/AMENDMENT.md.

The Modal container regenerates the A0 question pool on the raw base and extracts
dual-position hidden states, then grades answerable rows. The inputs it needs
(question text, aliases for grading, gold_class, category flavor, and the frozen
`score_L24` used by the residual rule) live in UNTRACKED / gitignored analysis
artifacts on the host (`ah_stage0/expansion/pool_v21.jsonl` + the two candidate
files that carry aliases). A cloned repo in the container does NOT contain them.

This builder joins those host artifacts into ONE self-contained pool file the
container fetches from the private staging repo. It never contains FalseQA text
and is not committed (analysis outputs are gitignored); it is uploaded to the
staging repo under the AM run prefix at launch time.

Each emitted row carries exactly what the container needs and nothing derived on
the GPU:
  row_key, safe_key, question, aliases, gold_class, category_canon, score_L24

`score_L24` is the frozen pre-generation scalar from the cached A0 extraction; it
is an INPUT to the deterministic residual rule (score_L24 >= 6.559), carried
through verbatim so the container never recomputes it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from path_compat import phase1_probe_dir  # noqa: E402

PROBE_DIR = phase1_probe_dir()
ANALYSIS = PROBE_DIR / "analysis"
STAGE0 = ANALYSIS / "ah_stage0"
DEFAULT_POOL = STAGE0 / "expansion" / "pool_v21.jsonl"
CAND_FILES = [
    STAGE0 / "candidates.jsonl",
    STAGE0 / "expansion" / "expansion_candidates.jsonl",
]
DEFAULT_OUT = ANALYSIS / "am_residual_catch" / "am_pool.jsonl"
EXPECTED_POOL = 1662


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def load_candidate_lookup():
    """row_key -> {question, aliases} joined from both candidate files (AH lineage)."""
    lut = {}
    for f in CAND_FILES:
        if not f.is_file():
            raise SystemExit(f"[am/pool] missing candidate file {f}")
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
        raise SystemExit(f"[am/pool] pool has {len(pool)} rows, expected {EXPECTED_POOL}")
    lut = load_candidate_lookup()
    missing = [r["row_key"] for r in pool if r["row_key"] not in lut]
    if missing:
        raise SystemExit(f"[am/pool] {len(missing)} rows missing question/aliases; "
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
                "score_L24": r["score_L24"],
            }, ensure_ascii=False) + "\n")

    print(f"[am/pool] wrote {len(pool)} rows -> {out_path}", flush=True)
    print(f"[am/pool] answerable={n_answerable} (with aliases={n_alias})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
