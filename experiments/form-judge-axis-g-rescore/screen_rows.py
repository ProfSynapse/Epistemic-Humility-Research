#!/usr/bin/env python3
"""Priority screen for form-judge-axis-g-rescore.

Reads the naming battery's 7 merged Arm A runlogs (read-only; path taken via
`--runlog-dir`, defaulting to the sibling
`write-direction-naming-battery/analysis/runlog_form_merged/` directory) and
applies the deterministic F5/F4 priority screen from AMENDMENT.md "Design"
(`screen_lib.classify_screen`, the SINGLE place that logic lives -- see its
module docstring). Only the F5/F4 field checks run here; F1/F2/F3 is never
assigned by this script, that is the judge lane's job.

Emits:
  (a) per-sub-arm screen counts, ID-free (no row_key, no text), written to
      `analysis/screen_counts.json`. TODO(post-sign): once this cell is
      signed, move this summary to `analysis-committed/screen_counts.json`
      (the AMENDMENT.md convention for other cells' committed count
      summaries) -- writing to `analysis/` for now because the cell is still
      DRAFT and nothing should land in analysis-committed/ before sign.
  (b) the screened-in remainder rows (row_key, arm, text) to
      `analysis/screened_in/<arm>.jsonl`, one file per sub-arm. Skipped
      entirely in `--count-only` mode.

`--count-only` computes and reports the counts without writing any row-level
text anywhere (not even to the gitignored `analysis/` dir): used for the
harness-build dry run so no real generation text is written to disk before
the cell is signed and scored grading is authorized.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import screen_lib

HERE = Path(__file__).resolve().parent
DEFAULT_RUNLOG_DIR = HERE.parent / "write-direction-naming-battery" / "analysis" / "runlog_form_merged"
DEFAULT_OUT_DIR = HERE / "analysis"


def cmd_screen(args: argparse.Namespace) -> int:
    runlog_dir = Path(args.runlog_dir) if args.runlog_dir else DEFAULT_RUNLOG_DIR
    out_dir = Path(args.out_dir) if args.out_dir else DEFAULT_OUT_DIR

    screened, coverage = screen_lib.load_and_screen(runlog_dir)

    per_arm_counts: dict[str, dict[str, int]] = {}
    totals = {"n_total": 0, "n_f5_degenerate": 0, "n_f4_explicit_idk": 0, "n_screened_in": 0}
    for arm in screen_lib.ALL_ARM_KEYS:
        buckets = screened[arm]
        n_f5 = len(buckets[screen_lib.F5_DEGENERATE])
        n_f4 = len(buckets[screen_lib.F4_EXPLICIT_IDK])
        n_screened_in = len(buckets[screen_lib.SCREENED_IN])
        n_total = n_f5 + n_f4 + n_screened_in
        per_arm_counts[arm] = {
            "n_total": n_total,
            "n_f5_degenerate": n_f5,
            "n_f4_explicit_idk": n_f4,
            "n_screened_in": n_screened_in,
        }
        totals["n_total"] += n_total
        totals["n_f5_degenerate"] += n_f5
        totals["n_f4_explicit_idk"] += n_f4
        totals["n_screened_in"] += n_screened_in

    summary = {
        "cell": "form_judge_axis_g_rescore",
        "runlog_dir": str(runlog_dir),
        "coverage": coverage,
        "per_arm": per_arm_counts,
        "totals": totals,
        "count_only": bool(args.count_only),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    screen_lib.write_json(out_dir / "screen_counts.json", summary)

    if not args.count_only:
        screened_in_dir = out_dir / "screened_in"
        for arm in screen_lib.ALL_ARM_KEYS:
            screen_lib.write_jsonl(screened_in_dir / f"{arm}.jsonl", screened[arm][screen_lib.SCREENED_IN])

    print(json.dumps(summary, indent=2, default=str), flush=True)
    if args.count_only:
        print(
            "\n[screen_rows] count-only mode: screen_counts.json written; NO "
            "screened_in/<arm>.jsonl text files were written.",
            flush=True,
        )
    else:
        print(
            f"\n[screen_rows] wrote screen_counts.json and screened_in/*.jsonl under {out_dir} "
            "(gitignored).",
            flush=True,
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runlog-dir", default=None, help=f"default: {DEFAULT_RUNLOG_DIR}")
    ap.add_argument("--out-dir", default=None, help=f"default: {DEFAULT_OUT_DIR}")
    ap.add_argument("--count-only", action="store_true", help="write counts only; skip screened_in/*.jsonl text output")
    ap.set_defaults(func=cmd_screen)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
