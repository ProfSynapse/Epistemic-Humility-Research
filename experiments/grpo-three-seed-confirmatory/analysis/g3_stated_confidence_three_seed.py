#!/usr/bin/env python3
"""Three-seed stated-confidence summary for the grpo-three-seed-confirmatory
block, extending G3 (which covers only the six behavioral metrics) to the
stated_confidence block that paper 2 Section 5 draws on.

Scope: all eight response-confidence-track arms defined in cell.yaml
(clean_sft base + clean_sft_dpo + clean_sft_kto + the five GRPO-touching
arms), not just the five "GRPO-touching" arms g3_three_seed_intervals.py
covers -- Section 5's flat-~0.82 claim is about the whole track.

Seed 2/3: read directly from on-disk metrics.json (`stated_confidence` block)
under archive/experiment/phase1/eval/results_grpo3seed_response_confidence_*.
By-outcome breakdown (known_answered_wrong / known_correct_answered /
known_refused / unknown_answered_wrong / unknown_refused) is computed from the
row-level scored_rows.jsonl beside each metrics.json (fields: label, refused,
correct, stated_confidence) -- these files are local scratch, never committed,
per the amendment's data-containment rule. This script's OUTPUT contains only
aggregate numbers (counts, means, CIs), never row content.

Seed 1: the raw per-seed metrics.json files for the response-confidence track
are NOT present on disk or in git history (same finding g3_three_seed_intervals.py
already recorded). Two seed-1 sources exist, at different granularity:
  (a) archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
      -- has mean_confidence, mean_confidence_coverage_pct,
      mean_brier_vs_response_appropriateness for all 8 arms (Amendment E/F rows).
      Missing: mae_vs_response_appropriateness and all *_vs_known_label /
      *_vs_answer_correctness fields (not columns in this CSV).
  (b) archive/experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json
      -- has a by-outcome breakdown (per_cell_emitted_mean), but ONLY for
      clean_sft_grpo_v2. No equivalent file exists for the other 7 arms.
Both gaps are reported as gaps, not imputed.

Bootstrap: same seed-level bootstrap as g3_three_seed_intervals.py --
resample the 3 seed-level scalar values with replacement, n_resamples=10000,
random_state=12345. This is a small-sample descriptive object (n=3), not an
inferential one, matching the repo's existing G3 convention for this block.
"""
import csv
import json
import random
from pathlib import Path

REPO = Path("/home/profsynapse/code/Epistemic-Humility-Research")
EVAL = REPO / "archive/experiment/phase1/eval"
OUT_DIR = REPO / "experiments/grpo-three-seed-confirmatory/analysis"

SEED1_CSV = EVAL / "analysis/selfaware_full_run_comparison_grouped.csv"
SEED1_CALIB_GRPO_V2 = EVAL / "analysis/calibration_gap_clean_sft_grpo_v2_seed1.json"

STATED_CONF_FIELDS = [
    "mean_stated_confidence",
    "coverage_pct",
    "mae_vs_known_label",
    "brier_vs_known_label",
    "mae_vs_answer_correctness",
    "brier_vs_answer_correctness",
    "mae_vs_response_appropriateness",
    "brier_vs_response_appropriateness",
]

OUTCOME_CELLS = [
    "known_answered_wrong",
    "known_correct_answered",
    "known_refused",
    "unknown_answered_wrong",
    "unknown_refused",
]

# All eight response-confidence-track arms (cell.yaml `arms:`), full-eval dirs
# for seed 2/3. Naming follows the on-disk convention confirmed by `find`.
ARMS_SEED23 = {
    "clean_sft_merged": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_seed2_merged_full_4b/clean_schema_sft_merged_seed2__selfaware",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_seed3_merged_full_4b/clean_schema_sft_merged_seed3__selfaware",
    },
    "clean_sft_dpo": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_seed2_full_4b/clean_schema_sft_dpo_seed2__selfaware",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_seed3_full_4b/clean_schema_sft_dpo_seed3__selfaware",
    },
    "clean_sft_kto": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_kto_seed2_full_4b/clean_schema_sft_kto_seed2__selfaware",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_kto_seed3_full_4b/clean_schema_sft_kto_seed3__selfaware",
    },
    "clean_sft_grpo_v2": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_full_4b/clean_schema_sft_grpo_v2_seed2__selfaware",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed3_full_4b/clean_schema_sft_grpo_v2_seed3__selfaware",
    },
    "clean_sft_dpo_grpo": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_grpo_seed2_full_4b/clean_sft_dpo_grpo_seed2__selfaware",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_grpo_seed3_full_4b/clean_sft_dpo_grpo_seed3__selfaware",
    },
    "clean_sft_kto_grpo": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_kto_grpo_seed2_full_4b/clean_sft_kto_grpo_seed2__selfaware",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_kto_grpo_seed3_full_4b/clean_sft_kto_grpo_seed3__selfaware",
    },
    "clean_sft_grpo_dpo": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_dpo_seed2_full_4b/clean_sft_grpo_dpo_seed2__selfaware",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_dpo_seed3_full_4b/clean_sft_grpo_dpo_seed3__selfaware",
    },
    "clean_sft_grpo_kto": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_kto_seed2_full_4b/clean_sft_grpo_kto_seed2__selfaware",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_kto_seed3_full_4b/clean_sft_grpo_kto_seed3__selfaware",
    },
}

# normalized_arm value in the seed-1 CSV for each arm above.
SEED1_CSV_ARM = {
    "clean_sft_merged": "clean_sft_merged",
    "clean_sft_dpo": "clean_sft_dpo",
    "clean_sft_kto": "clean_sft_kto",
    "clean_sft_grpo_v2": "clean_sft_grpo_v2",
    "clean_sft_dpo_grpo": "clean_sft_dpo_grpo",
    "clean_sft_kto_grpo": "clean_sft_kto_grpo",
    "clean_sft_grpo_dpo": "clean_sft_grpo_dpo",
    "clean_sft_grpo_kto": "clean_sft_grpo_kto",
}


def bootstrap_ci(values, n_resamples=10000, seed=12345, level=0.95):
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(n_resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    alpha = 1 - level
    lo_idx = int((alpha / 2) * n_resamples)
    hi_idx = int((1 - alpha / 2) * n_resamples) - 1
    return means[lo_idx], means[hi_idx]


def load_seed23_metrics():
    data = {}
    flags = []
    for arm, seeds in ARMS_SEED23.items():
        data[arm] = {}
        for seed, rel in seeds.items():
            p = EVAL / rel / "metrics.json"
            if not p.exists():
                flags.append(f"MISSING metrics.json: arm={arm} seed={seed} path={p}")
                continue
            d = json.loads(p.read_text())
            sc = d.get("stated_confidence")
            if sc is None:
                flags.append(f"MISSING stated_confidence block: arm={arm} seed={seed} path={p}")
                continue
            row = {
                "mean_stated_confidence": sc["mean_stated_confidence"],
                "coverage_pct": sc["coverage_pct"],
                "mae_vs_known_label": sc["mae_vs_known_label"],
                "brier_vs_known_label": sc["brier_vs_known_label"],
                "mae_vs_answer_correctness": sc["mae_vs_answer_correctness"],
                "brier_vs_answer_correctness": sc["brier_vs_answer_correctness"],
                "mae_vs_response_appropriateness": sc["mae_vs_response_appropriateness"],
                "brier_vs_response_appropriateness": sc["brier_vs_response_appropriateness"],
                "_n": sc["n"],
                "_n_with_confidence": sc["n_with_confidence"],
                "_path": str(p.relative_to(REPO)),
            }
            data[arm][seed] = row
    return data, flags


def load_seed23_by_outcome():
    """Compute per-outcome-cell mean stated_confidence from row-level
    scored_rows.jsonl (label x refused x correct), mirroring the five cells
    the seed-1 calibration_gap file uses for clean_sft_grpo_v2."""
    data = {}
    flags = []
    for arm, seeds in ARMS_SEED23.items():
        data[arm] = {}
        for seed, rel in seeds.items():
            p = EVAL / rel / "scored_rows.jsonl"
            if not p.exists():
                flags.append(f"MISSING scored_rows.jsonl: arm={arm} seed={seed} path={p}")
                continue
            cells = {c: [] for c in OUTCOME_CELLS}
            n_rows = 0
            unmatched = 0
            with open(p) as f:
                for line in f:
                    row = json.loads(line)
                    n_rows += 1
                    label = row.get("label")
                    refused = row.get("refused")
                    correct = row.get("correct")
                    conf = row.get("stated_confidence")
                    if conf is None:
                        continue
                    if label == "known" and refused is False and correct is False:
                        cells["known_answered_wrong"].append(conf)
                    elif label == "known" and refused is False and correct is True:
                        cells["known_correct_answered"].append(conf)
                    elif label == "known" and refused is True:
                        cells["known_refused"].append(conf)
                    elif label == "unknown" and refused is False:
                        cells["unknown_answered_wrong"].append(conf)
                    elif label == "unknown" and refused is True:
                        cells["unknown_refused"].append(conf)
                    else:
                        unmatched += 1
            if unmatched:
                flags.append(
                    f"UNMATCHED rows outside the 5 outcome cells: arm={arm} seed={seed} "
                    f"n_unmatched={unmatched} of n_rows={n_rows} path={p}"
                )
            summary = {}
            for c in OUTCOME_CELLS:
                vals = cells[c]
                summary[c] = {
                    "n": len(vals),
                    "mean": (sum(vals) / len(vals)) if vals else None,
                }
            summary["_n_rows"] = n_rows
            summary["_path"] = str(p.relative_to(REPO))
            data[arm][seed] = summary
    return data, flags


def load_seed1_csv():
    rows = {}
    with open(SEED1_CSV) as f:
        for r in csv.DictReader(f):
            arm = r["normalized_arm"]
            if arm in SEED1_CSV_ARM.values():
                rows[arm] = {
                    "mean_stated_confidence": float(r["mean_mean_confidence"]) if r["mean_mean_confidence"] else None,
                    "coverage_pct": float(r["mean_confidence_coverage_pct"]) if r["mean_confidence_coverage_pct"] else None,
                    "brier_vs_response_appropriateness": float(r["mean_brier_vs_response_appropriateness"]) if r["mean_brier_vs_response_appropriateness"] else None,
                    "mae_vs_known_label": None,
                    "brier_vs_known_label": None,
                    "mae_vs_answer_correctness": None,
                    "brier_vs_answer_correctness": None,
                    "mae_vs_response_appropriateness": None,
                    "_n_runs": r["n_runs"],
                    "_source_metrics_referenced": r["source_metrics"],
                }
    return rows


def load_seed1_by_outcome_grpo_v2():
    d = json.loads(SEED1_CALIB_GRPO_V2.read_text())
    cells = d["A_full_eval"]["per_cell_emitted_mean"]
    summary = {}
    for c in OUTCOME_CELLS:
        cell = cells.get(c)
        summary[c] = {"n": cell["n"], "mean": cell["mean"]} if cell else {"n": None, "mean": None}
    summary["_source"] = str(SEED1_CALIB_GRPO_V2.relative_to(REPO))
    summary["_source_scored_rows_referenced"] = d["scored_rows"]
    return summary


def main():
    seed23, flags1 = load_seed23_metrics()
    seed23_outcome, flags2 = load_seed23_by_outcome()
    seed1 = load_seed1_csv()
    seed1_outcome_grpo_v2 = load_seed1_by_outcome_grpo_v2()
    flags = flags1 + flags2

    result = {
        "description": "Three-seed stated-confidence summary, grpo-three-seed-confirmatory block. "
                        "Exploratory response-confidence track (not the PROTOCOL v0.3 headline). "
                        "See docstring of this script for seed-1 data-gap details.",
        "bootstrap": {"method": "seed-level resample with replacement", "n_resamples": 10000, "random_state": 12345, "level": 0.95},
        "arms": {},
        "by_outcome": {},
        "flags": flags,
    }

    for arm in ARMS_SEED23:
        s1 = seed1.get(arm, {})
        s2 = seed23.get(arm, {}).get(2, {})
        s3 = seed23.get(arm, {}).get(3, {})
        arm_out = {"per_seed": {"seed1": s1, "seed2": s2, "seed3": s3}, "three_seed": {}}
        for field in STATED_CONF_FIELDS:
            v1 = s1.get(field)
            v2 = s2.get(field)
            v3 = s3.get(field)
            if v1 is None or v2 is None or v3 is None:
                present = {f"seed{i+1}": v for i, v in enumerate([v1, v2, v3]) if v is not None}
                arm_out["three_seed"][field] = {"status": "INCOMPLETE_missing_seed", "available": present}
                continue
            vals = [v1, v2, v3]
            mean = sum(vals) / 3
            lo, hi = bootstrap_ci(vals)
            arm_out["three_seed"][field] = {"mean": mean, "ci95": [lo, hi], "values": vals}
        result["arms"][arm] = arm_out

    # By-outcome: seed2/3 computed for all arms; seed1 only available for clean_sft_grpo_v2.
    for arm in ARMS_SEED23:
        s2 = seed23_outcome.get(arm, {}).get(2, {})
        s3 = seed23_outcome.get(arm, {}).get(3, {})
        entry = {"seed2": s2, "seed3": s3}
        if arm == "clean_sft_grpo_v2":
            entry["seed1"] = seed1_outcome_grpo_v2
            entry["three_seed"] = {}
            for c in OUTCOME_CELLS:
                v1 = seed1_outcome_grpo_v2.get(c, {}).get("mean")
                v2 = s2.get(c, {}).get("mean")
                v3 = s3.get(c, {}).get("mean")
                if v1 is None or v2 is None or v3 is None:
                    entry["three_seed"][c] = {"status": "INCOMPLETE_missing_seed"}
                    continue
                vals = [v1, v2, v3]
                mean = sum(vals) / 3
                lo, hi = bootstrap_ci(vals)
                entry["three_seed"][c] = {"mean": mean, "ci95": [lo, hi], "values": vals}
        else:
            entry["seed1"] = "NOT AVAILABLE: no calibration_gap_*.json exists for this arm at seed 1"
        result["by_outcome"][arm] = entry

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "g3_stated_confidence_three_seed.json"
    out_json.write_text(json.dumps(result, indent=2))

    # CSV: arm x field -> mean, ci_lo, ci_hi, seed1, seed2, seed3
    out_csv = OUT_DIR / "g3_stated_confidence_three_seed.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arm", "field", "seed1", "seed2", "seed3", "three_seed_mean", "ci95_lo", "ci95_hi", "status"])
        for arm, arm_out in result["arms"].items():
            ps = arm_out["per_seed"]
            for field in STATED_CONF_FIELDS:
                v1 = ps["seed1"].get(field)
                v2 = ps["seed2"].get(field)
                v3 = ps["seed3"].get(field)
                ts = arm_out["three_seed"].get(field, {})
                if "mean" in ts:
                    w.writerow([arm, field, v1, v2, v3, ts["mean"], ts["ci95"][0], ts["ci95"][1], "OK"])
                else:
                    w.writerow([arm, field, v1, v2, v3, "", "", "", "INCOMPLETE"])
        w.writerow([])
        w.writerow(["arm", "outcome_cell", "seed1_mean", "seed1_n", "seed2_mean", "seed2_n", "seed3_mean", "seed3_n", "three_seed_mean", "ci95_lo", "ci95_hi"])
        for arm, entry in result["by_outcome"].items():
            s1 = entry.get("seed1")
            for c in OUTCOME_CELLS:
                s1c = s1.get(c, {}) if isinstance(s1, dict) else {}
                s2c = entry.get("seed2", {}).get(c, {})
                s3c = entry.get("seed3", {}).get(c, {})
                ts = entry.get("three_seed", {}).get(c, {}) if "three_seed" in entry else {}
                w.writerow([
                    arm, c,
                    s1c.get("mean"), s1c.get("n"),
                    s2c.get("mean"), s2c.get("n"),
                    s3c.get("mean"), s3c.get("n"),
                    ts.get("mean", ""), ts.get("ci95", ["", ""])[0] if "ci95" in ts else "", ts.get("ci95", ["", ""])[1] if "ci95" in ts else "",
                ])

    print(f"Wrote {out_json}")
    print(f"Wrote {out_csv}")
    print(f"Flags: {len(flags)}")
    for fl in flags:
        print(f"  {fl}")


if __name__ == "__main__":
    main()
