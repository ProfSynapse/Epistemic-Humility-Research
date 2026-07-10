#!/usr/bin/env python3
"""AL prep: grade the A0-surface generations (TRUE + PERMUTED arms), CPU-only.

The local A0 cells (amendment_ai_verdict_extract_gen.py --stage generate)
ship raw rows with behavioral flags (answered/refused/degenerate) but no
correctness grading. This script joins each arm's rows with the pool
(gold_class/label/source/category) and the AH candidate files (question +
aliases), then applies the AH-lineage grading (Cheng scorers.is_correct on
gold-answerable rows carrying aliases; confab_on_unanswerable = answered a
gold-unanswerable question). Output: graded rows per arm plus a compact
summary JSON for the AL ceiling table.

Usage:
  python amendment_al_prep_grade_a0_generations.py \
      [--arms true_a0,permuted_a0] [--al-prep-dir <analysis/amendment_al_prep>]
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ARCHIVE_AMENDMENTS_DIR = Path(__file__).resolve().parent
if str(ARCHIVE_AMENDMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_AMENDMENTS_DIR))

from path_compat import phase1_eval_dir, phase1_probe_dir, repo_root  # noqa: E402

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402

CANONICAL = repo_root()
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
CAND_FILES = [STAGE0 / "candidates.jsonl",
              STAGE0 / "expansion/expansion_candidates.jsonl"]
DEFAULT_AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
EXPECTED_ROWS = 1662


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arms", default="true_a0,permuted_a0")
    ap.add_argument("--al-prep-dir", default=str(DEFAULT_AL_PREP))
    args = ap.parse_args()

    al_prep = Path(args.al_prep_dir)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    cand = {}
    for f in CAND_FILES:
        for r in load_jsonl(f):
            cand[r["row_key"]] = {"question": r["question"],
                                  "aliases": r.get("aliases", [])}

    # every arm ran on the same joined pool file (written by the permuted cell)
    pool = {r["row_key"]: r for r in load_jsonl(al_prep / "permuted_a0/pool.jsonl")}
    assert len(pool) == EXPECTED_ROWS, f"pool has {len(pool)} rows"

    summary = {}
    for arm in arms:
        rows_path = al_prep / arm / "gen/data/rows.jsonl"
        rows = load_jsonl(rows_path)
        assert len(rows) == EXPECTED_ROWS, f"{arm}: {len(rows)} rows"

        counts = defaultdict(int)
        by_class = {"answerable": defaultdict(int),
                    "unanswerable": defaultdict(int)}
        graded_path = al_prep / arm / "gen/data/rows_graded.jsonl"
        with graded_path.open("w") as out:
            for r in rows:
                p = pool[r["row_key"]]
                c = cand[r["row_key"]]
                is_answerable = (p["gold_class"] == "answerable")
                cls = "answerable" if is_answerable else "unanswerable"
                aliases = c["aliases"]

                correct = None
                if is_answerable and aliases and r["answered"]:
                    correct = bool(scorers.is_correct(r["answer_text"], aliases))
                confab = bool(r["answered"] and not is_answerable)

                counts["n"] += 1
                by_class[cls]["n"] += 1
                for flag in ("answered", "refused", "degenerate"):
                    if r.get(flag):
                        counts[flag] += 1
                        by_class[cls][flag] += 1
                if correct is True:
                    counts["correct"] += 1
                    by_class[cls]["correct"] += 1
                if correct is not None:
                    counts["graded"] += 1
                    by_class[cls]["graded"] += 1
                if confab:
                    counts["confab_on_unanswerable"] += 1
                    by_class[cls]["confab_on_unanswerable"] += 1

                out.write(json.dumps({
                    **{k: p.get(k) for k in ("label", "source", "gold_class",
                                             "category_canon")},
                    "question": c["question"], "aliases": aliases,
                    **r,
                    "correct": correct,
                    "confab_on_unanswerable": confab,
                }, ensure_ascii=False) + "\n")

        arm_summary = {
            "rows_file": str(graded_path),
            "overall": dict(counts),
            "by_gold_class": {k: dict(v) for k, v in by_class.items()},
        }
        ans = arm_summary["by_gold_class"]["answerable"]
        una = arm_summary["by_gold_class"]["unanswerable"]
        arm_summary["rates"] = {
            "answer_rate_answerable": round(ans["answered"] / max(ans["n"], 1), 4),
            "correct_among_graded": round(
                ans.get("correct", 0) / max(ans.get("graded", 0), 1), 4),
            "refuse_rate_unanswerable": round(
                una["refused"] / max(una["n"], 1), 4),
            "confab_rate_unanswerable": round(
                una.get("confab_on_unanswerable", 0) / max(una["n"], 1), 4),
        }
        summary[arm] = arm_summary
        print(f"[{arm}] {json.dumps(arm_summary['rates'])}")

    report = al_prep / "a0_generation_grading_report.json"
    report.write_text(json.dumps(summary, indent=2))
    print(f"[grade-a0] report -> {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
