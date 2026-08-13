#!/usr/bin/env python3
"""Seed-1 gap recovery for the stated-confidence three-seed table.

g3_stated_confidence_three_seed.py (2026-08-13 descriptive addition) recorded
a known gap: seed-1 raw metrics.json for the response-confidence track was not
found on disk under archive/experiment/phase1/eval/ (those results_*/ dirs are
gitignored local scratch and were never force-added), so the extended fields
(mae/brier vs known_label and vs answer_correctness, mae vs
response_appropriateness) and the by-outcome breakdown for 7 of 8 arms carried
seed2/3 only.

This script closes that gap. A repo-wide sweep (PI-requested recovery pass,
2026-08-13) found that all 8 arms' seed-1 full SelfAware eval outputs
(metrics.json AND row-level scored_rows.jsonl, 3369 rows each) survive as
"phase1-migrated" copies under the two experiments that originally ran them:

  experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/
    results_amendment_e_response_confidence_selfaware_<arm>_full_4b/.../metrics.json
  experiments/grpo-centered-stacking/analysis/phase1-migrated/eval/
    results_amendment_f_response_confidence_selfaware_<arm>_full_4b/.../metrics.json

These metrics.json files already carry the full stated_confidence block
(scorers.stated_confidence_summary, archive/experiment/phase1/eval/scorers.py:
371-458) -- no re-parsing of raw generations is needed, the fields are read
directly, exactly as g3_stated_confidence_three_seed.py's
load_seed23_metrics() reads seed 2/3. Verified before use: mean_stated_confidence
and brier_vs_response_appropriateness in every one of these 8 metrics.json
files match the seed-1 values already in the committed three-seed JSON/CSV
(sourced from selfaware_full_run_comparison_grouped.csv) to 6 decimal places --
same run, not a different one.

By-outcome breakdown is computed from scored_rows.jsonl (fields: label,
refused, correct, stated_confidence), mirroring
g3_stated_confidence_three_seed.py's load_seed23_by_outcome() cell definitions
exactly. Verified before use: the clean_sft_grpo_v2 recomputation matches
calibration_gap_clean_sft_grpo_v2_seed1.json's per_cell_emitted_mean exactly
(0.82001.../0.82223.../0.81092.../0.81235.../0.81108...).

Bootstrap convention unchanged from g3_stated_confidence_three_seed.py:
seed-level resample with replacement, n_resamples=10000, random_state=12345.

Output: experiments/grpo-three-seed-confirmatory/analysis/
  g3_stated_confidence_three_seed_v2.{json,csv}
Numbers/labels only (containment-clean); no question or generation text is
written out.
"""
import csv
import json
import random
from pathlib import Path

REPO = Path("/home/profsynapse/code/Epistemic-Humility-Research")
OUT_DIR = REPO / "experiments/grpo-three-seed-confirmatory/analysis"

V1_JSON = OUT_DIR / "g3_stated_confidence_three_seed.json"

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

# Seed-1 full-eval dirs recovered from the phase1-migrated copies (verified to
# exist with both metrics.json and scored_rows.jsonl, 3369 rows each).
SEED1_DIRS = {
    "clean_sft_merged": REPO
    / "experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval"
    / "results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b"
    / "clean_schema_sft_merged_seed1__selfaware",
    "clean_sft_dpo": REPO
    / "experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval"
    / "results_amendment_e_response_confidence_selfaware_clean_sft_dpo_seed1_corrected_base_full_4b"
    / "clean_schema_sft_dpo_seed1_corrected_base__selfaware",
    "clean_sft_kto": REPO
    / "experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval"
    / "results_amendment_e_response_confidence_selfaware_clean_sft_kto_seed1_corrected_base_full_4b"
    / "clean_schema_sft_kto_seed1_corrected_base__selfaware",
    "clean_sft_grpo_v2": REPO
    / "experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval"
    / "results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b"
    / "clean_schema_sft_grpo_v2_seed1_corrected_base__selfaware",
    "clean_sft_dpo_grpo": REPO
    / "experiments/grpo-centered-stacking/analysis/phase1-migrated/eval"
    / "results_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_4b"
    / "clean_sft_dpo_grpo_seed1__selfaware",
    "clean_sft_kto_grpo": REPO
    / "experiments/grpo-centered-stacking/analysis/phase1-migrated/eval"
    / "results_amendment_f_response_confidence_selfaware_clean_sft_kto_grpo_seed1_full_4b"
    / "clean_sft_kto_grpo_seed1__selfaware",
    "clean_sft_grpo_dpo": REPO
    / "experiments/grpo-centered-stacking/analysis/phase1-migrated/eval"
    / "results_amendment_f_response_confidence_selfaware_clean_sft_grpo_dpo_seed1_full_4b"
    / "clean_sft_grpo_dpo_seed1__selfaware",
    "clean_sft_grpo_kto": REPO
    / "experiments/grpo-centered-stacking/analysis/phase1-migrated/eval"
    / "results_amendment_f_response_confidence_selfaware_clean_sft_grpo_kto_seed1_full_4b"
    / "clean_sft_grpo_kto_seed1__selfaware",
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


def load_seed1_metrics():
    data = {}
    flags = []
    for arm, d in SEED1_DIRS.items():
        p = d / "metrics.json"
        if not p.exists():
            flags.append(f"MISSING metrics.json: arm={arm} seed=1 path={p}")
            continue
        m = json.loads(p.read_text())
        sc = m.get("stated_confidence")
        if sc is None:
            flags.append(f"MISSING stated_confidence block: arm={arm} seed=1 path={p}")
            continue
        data[arm] = {
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
    return data, flags


def load_seed1_by_outcome():
    data = {}
    flags = []
    for arm, d in SEED1_DIRS.items():
        p = d / "scored_rows.jsonl"
        if not p.exists():
            flags.append(f"MISSING scored_rows.jsonl: arm={arm} seed=1 path={p}")
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
                f"UNMATCHED rows outside the 5 outcome cells: arm={arm} seed=1 "
                f"n_unmatched={unmatched} of n_rows={n_rows} path={p}"
            )
        summary = {}
        for c in OUTCOME_CELLS:
            vals = cells[c]
            summary[c] = {"n": len(vals), "mean": (sum(vals) / len(vals)) if vals else None}
        summary["_n_rows"] = n_rows
        summary["_path"] = str(p.relative_to(REPO))
        data[arm] = summary
    return data, flags


def main():
    v1 = json.loads(V1_JSON.read_text())
    seed1_metrics, flags1 = load_seed1_metrics()
    seed1_outcome, flags2 = load_seed1_by_outcome()
    flags = flags1 + flags2

    result = {
        "description": "Three-seed stated-confidence summary, grpo-three-seed-confirmatory "
        "block, v2 with the seed-1 data gap closed. Seed-1 recovered from the "
        "phase1-migrated copies of the amendment-e/f full SelfAware evals (see "
        "docstring of this script for provenance and verification). Exploratory "
        "response-confidence track (not the PROTOCOL v0.3 headline).",
        "bootstrap": {
            "method": "seed-level resample with replacement",
            "n_resamples": 10000,
            "random_state": 12345,
            "level": 0.95,
        },
        "seed1_recovery": {
            "recovered_from": "phase1-migrated copies (experiments/probe-scaled-response-confidence "
            "and experiments/grpo-centered-stacking); see script docstring",
            "verification": "mean_stated_confidence and brier_vs_response_appropriateness in every "
            "recovered metrics.json matched the pre-existing committed seed-1 values "
            "(sourced from selfaware_full_run_comparison_grouped.csv) exactly for all 8 arms; "
            "clean_sft_grpo_v2 by-outcome recomputation matched "
            "calibration_gap_clean_sft_grpo_v2_seed1.json exactly",
        },
        "arms": {},
        "by_outcome": {},
        "flags": flags,
    }

    for arm in SEED1_DIRS:
        s1 = seed1_metrics.get(arm, {})
        s2 = v1["arms"][arm]["per_seed"]["seed2"]
        s3 = v1["arms"][arm]["per_seed"]["seed3"]
        arm_out = {"per_seed": {"seed1": s1, "seed2": s2, "seed3": s3}, "three_seed": {}}
        for field in STATED_CONF_FIELDS:
            v1_, v2_, v3_ = s1.get(field), s2.get(field), s3.get(field)
            if v1_ is None or v2_ is None or v3_ is None:
                present = {f"seed{i+1}": v for i, v in enumerate([v1_, v2_, v3_]) if v is not None}
                arm_out["three_seed"][field] = {"status": "INCOMPLETE_missing_seed", "available": present}
                continue
            vals = [v1_, v2_, v3_]
            mean = sum(vals) / 3
            lo, hi = bootstrap_ci(vals)
            arm_out["three_seed"][field] = {"mean": mean, "ci95": [lo, hi], "values": vals}
        result["arms"][arm] = arm_out

    for arm in SEED1_DIRS:
        s1 = seed1_outcome.get(arm, {})
        s2 = v1["by_outcome"][arm].get("seed2", {})
        s3 = v1["by_outcome"][arm].get("seed3", {})
        entry = {"seed1": s1, "seed2": s2, "seed3": s3, "three_seed": {}}
        for c in OUTCOME_CELLS:
            v1_ = s1.get(c, {}).get("mean")
            v2_ = s2.get(c, {}).get("mean")
            v3_ = s3.get(c, {}).get("mean")
            if v1_ is None or v2_ is None or v3_ is None:
                entry["three_seed"][c] = {"status": "INCOMPLETE_missing_seed"}
                continue
            vals = [v1_, v2_, v3_]
            mean = sum(vals) / 3
            lo, hi = bootstrap_ci(vals)
            entry["three_seed"][c] = {"mean": mean, "ci95": [lo, hi], "values": vals}
        result["by_outcome"][arm] = entry

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "g3_stated_confidence_three_seed_v2.json"
    out_json.write_text(json.dumps(result, indent=2))

    out_csv = OUT_DIR / "g3_stated_confidence_three_seed_v2.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arm", "field", "seed1", "seed2", "seed3", "three_seed_mean", "ci95_lo", "ci95_hi", "status"])
        for arm, arm_out in result["arms"].items():
            ps = arm_out["per_seed"]
            for field in STATED_CONF_FIELDS:
                v1_ = ps["seed1"].get(field)
                v2_ = ps["seed2"].get(field)
                v3_ = ps["seed3"].get(field)
                ts = arm_out["three_seed"].get(field, {})
                if "mean" in ts:
                    w.writerow([arm, field, v1_, v2_, v3_, ts["mean"], ts["ci95"][0], ts["ci95"][1], "OK"])
                else:
                    w.writerow([arm, field, v1_, v2_, v3_, "", "", "", "INCOMPLETE"])
        w.writerow([])
        w.writerow(
            [
                "arm",
                "outcome_cell",
                "seed1_mean",
                "seed1_n",
                "seed2_mean",
                "seed2_n",
                "seed3_mean",
                "seed3_n",
                "three_seed_mean",
                "ci95_lo",
                "ci95_hi",
            ]
        )
        for arm, entry in result["by_outcome"].items():
            for c in OUTCOME_CELLS:
                s1c = entry.get("seed1", {}).get(c, {})
                s2c = entry.get("seed2", {}).get(c, {})
                s3c = entry.get("seed3", {}).get(c, {})
                ts = entry.get("three_seed", {}).get(c, {})
                w.writerow(
                    [
                        arm,
                        c,
                        s1c.get("mean"),
                        s1c.get("n"),
                        s2c.get("mean"),
                        s2c.get("n"),
                        s3c.get("mean"),
                        s3c.get("n"),
                        ts.get("mean", ""),
                        ts.get("ci95", ["", ""])[0] if "ci95" in ts else "",
                        ts.get("ci95", ["", ""])[1] if "ci95" in ts else "",
                    ]
                )

    print(f"Wrote {out_json}")
    print(f"Wrote {out_csv}")
    print(f"Flags: {len(flags)}")
    for fl in flags:
        print(f"  {fl}")


if __name__ == "__main__":
    main()
