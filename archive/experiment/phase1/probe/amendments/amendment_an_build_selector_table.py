#!/usr/bin/env python3
"""Build the Amendment AN propensity-selector operating table (CPU, deterministic).

AN is PROPENSITY-SELECTED, CAUTION-ACTUATED: flag rows with the confabulation-
propensity readout (the sensor AL proved has real reach into the confab cloud),
then correct them by writing the caution setpoint UP (AC's erase-and-write
mechanism). This script sizes the SELECTOR half: for a grid of propensity-z
selection thresholds, how many of the 116 baseline confabs are flagged (the
reach ceiling) and how many of the 90 baseline-correct answers are flagged (the
collateral exposure), plus flagged wrong / answerable-refused / unanswerable-
refused for context.

Input is AL's frozen A0 per-row exhaust (per_row_exhaust.jsonl): each row
carries prop_z (frozen propensity z-score), caution_z, gold_class, and the
baseline grade (answered/refused/correct/confab). The baseline grade split is
the AL-frozen 116 confab / 90 correct / 120 wrong / 114 answerable-refused /
1222 unanswerable-refused surface; AN reuses it, no re-baseline.

The chosen operating point is picked conservatively (aim-small-miss-small: keep
flagged-correct collateral exposure small while retaining a workable confab
reach) and marked in the output. The exact numbers at the chosen threshold are
pre-registration constants that get copied INTO the amendment doc.

Usage:
  python archive/experiment/phase1/probe/amendments/amendment_an_build_selector_table.py \
      --exhaust <per_row_exhaust.jsonl> --out-dir <amendment_an_prep>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from path_compat import phase1_probe_dir

PROBE_DIR = phase1_probe_dir()
DEFAULT_EXHAUST = (PROBE_DIR
                   / "analysis/amendment_al_prep/amendment_al_run/per_row_exhaust.jsonl")
DEFAULT_OUT = (PROBE_DIR / "analysis/amendment_an_prep")

# Selection threshold grid on propensity z-score (row flagged iff prop_z >= t).
# Spans from AL's chosen operating point (1.5484) down to where collateral grows.
GRID = [round(x, 2) for x in
        [2.00, 1.75, 1.5484, 1.50, 1.25, 1.00, 0.90, 0.80, 0.75, 0.70,
         0.656, 0.60, 0.50, 0.40, 0.30, 0.25, 0.00]]

# Pre-registered operating point (see doc §4 derivation). Chosen conservatively
# at the reach/collateral efficiency knee: prop_z >= 1.00 flags 47 confabs
# (40.5% reach) for only 4 flagged corrects (4.4% collateral exposure). Below
# 1.00 the marginal confab-per-collateral efficiency collapses (0.80 buys zero
# additional confabs for +1 correct); above it reach falls off fast (1.55 flags
# only 30 confabs). AL's own threshold was 1.5484; AN reaches deeper at a
# controlled collateral cost.
CHOSEN_THRESHOLD = 1.00


def grade(r: dict) -> str:
    b = r["baseline"]
    if b["confab"]:
        return "confab"
    if b["answered"]:
        return "correct" if b["correct"] else "wrong"
    if b["refused"]:
        return "answerable_refused" if r["gold_class"] == "answerable" else "unanswerable_refused"
    return "other"


GRADES = ["confab", "correct", "wrong", "answerable_refused", "unanswerable_refused"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exhaust", type=Path, default=DEFAULT_EXHAUST)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--chosen", type=float, default=CHOSEN_THRESHOLD)
    args = ap.parse_args()

    rows = [json.loads(l) for l in args.exhaust.open() if l.strip()]
    graded = [(grade(r), float(r["prop_z"])) for r in rows]
    totals = {g: sum(1 for gg, _ in graded if gg == g) for g in GRADES}

    table = []
    for t in GRID:
        flagged = {g: sum(1 for gg, z in graded if gg == g and z >= t) for g in GRADES}
        n_flag = sum(flagged.values())
        row = {
            "threshold": t,
            "n_flagged_total": n_flag,
            "flagged": flagged,
            "flagged_confab": flagged["confab"],
            "flagged_correct": flagged["correct"],
            "confab_reach_frac": round(flagged["confab"] / totals["confab"], 4),
            "correct_collateral_frac": round(flagged["correct"] / totals["correct"], 4),
            "is_chosen": abs(t - args.chosen) < 1e-9,
        }
        table.append(row)

    out = {
        "schema_version": "amendment-an-selector-table/v1",
        "source_exhaust": str(args.exhaust),
        "baseline_totals": totals,
        "chosen_threshold": args.chosen,
        "grid": GRID,
        "table": table,
        "notice": ("Propensity-selector sizing for Amendment AN. Row flagged iff "
                   "prop_z >= threshold. flagged_confab = reach ceiling; "
                   "flagged_correct = collateral exposure. Baseline grades are "
                   "AL's frozen A0 surface, reused."),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "an_selector_table.json").write_text(json.dumps(out, indent=2))

    # markdown
    lines = [
        "# Amendment AN - propensity-selector operating table",
        "",
        f"Source: `{args.exhaust}`",
        "",
        f"Baseline grade totals: confab={totals['confab']} correct={totals['correct']} "
        f"wrong={totals['wrong']} answerable_refused={totals['answerable_refused']} "
        f"unanswerable_refused={totals['unanswerable_refused']}",
        "",
        "Row flagged iff `prop_z >= threshold`. `confab` = reach ceiling; "
        "`correct` = collateral exposure.",
        "",
        "| thr | flag total | confab (reach) | correct (collateral) | wrong | ans-ref | unans-ref | reach% | collat% | chosen |",
        "|-----|-----------|----------------|----------------------|-------|---------|-----------|--------|---------|--------|",
    ]
    for r in table:
        f = r["flagged"]
        lines.append(
            f"| {r['threshold']:.4f} | {r['n_flagged_total']} | "
            f"{f['confab']} | {f['correct']} | {f['wrong']} | "
            f"{f['answerable_refused']} | {f['unanswerable_refused']} | "
            f"{r['confab_reach_frac']*100:.1f}% | {r['correct_collateral_frac']*100:.1f}% | "
            f"{'**<--**' if r['is_chosen'] else ''} |"
        )
    (args.out_dir / "an_selector_table.md").write_text("\n".join(lines) + "\n")

    # console summary at chosen threshold
    chosen = next(r for r in table if r["is_chosen"])
    print(f"baseline totals: {totals}")
    print(f"chosen threshold prop_z >= {args.chosen}:")
    print(f"  flagged confab (reach)     = {chosen['flagged']['confab']} / {totals['confab']} "
          f"({chosen['confab_reach_frac']*100:.1f}%)")
    print(f"  flagged correct (collateral)= {chosen['flagged']['correct']} / {totals['correct']} "
          f"({chosen['correct_collateral_frac']*100:.1f}%)")
    print(f"  flagged wrong               = {chosen['flagged']['wrong']}")
    print(f"  flagged answerable-refused  = {chosen['flagged']['answerable_refused']}")
    print(f"  flagged unanswerable-refused= {chosen['flagged']['unanswerable_refused']}")
    print(f"  n flagged total             = {chosen['n_flagged_total']}")
    print(f"wrote {args.out_dir/'an_selector_table.json'} and .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
