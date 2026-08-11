#!/usr/bin/env python3
"""G3 deliverable (grpo-three-seed-confirmatory): mean + 95% bootstrap CI
across seeds 1/2/3 for every GRPO-touching arm, on the six metrics gates.yaml
G3 names: truthful_pct, refusal_recall_pct, answer_on_unknown_pct,
over_refusal_pct, correct_on_known_pct, refusal_rate_pct.

Seed 2/3: read directly from on-disk metrics.json (full 3369-row eval,
uncommitted local scratch under archive/experiment/phase1/eval/results_grpo3seed_*).

Seed 1: the amendment_e/amendment_f seed-1 metrics.json files referenced by
source_metrics in the committed analysis CSV are NOT present on disk in this
checkout (git ls-files and git log --all --diff-filter=A both empty for those
paths -- they were computed once, force-added into that CSV as an aggregate,
but the underlying run directories were never committed and are not on local
scratch either). Per instruction, seed-1 numbers are taken from the artifact
closest to source that IS on disk: the committed aggregate CSV
archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
(n_runs=1 rows for the five GRPO-touching arms), not from AMENDMENT.md/gates.yaml
prose. That CSV carries percentages only, no raw counts, so correct_on_known_pct
denominators cannot be reconstructed for seed 1.

Bootstrap here resamples the THREE SEED-LEVEL VALUES with replacement (this is
what G3 literally specifies: "bootstrap CI across the three seeds"), which is a
different construction from the repo's row-level bootstrap convention used
elsewhere (10k resamples over rows for rate-difference CIs). With n=3 support
points, a seed-level bootstrap CI is a small-sample descriptive object, not an
inferential one -- consistent with gates.yaml calling G3 non-gating/descriptive.
n_resamples=10000, random_state=12345, fixed for reproducibility.
"""
import csv
import json
import random
from pathlib import Path

# Governed docs (gates.yaml, AMENDMENT.md) are read from the signed worktree;
# the seed-2/seed-3 metrics.json scratch artifacts only exist on-disk in the
# canonical checkout (results_* dirs are gitignored/never committed, and
# worktrees do not share untracked scratch files with each other).
DOCS_REPO = Path("/home/profsynapse/code/ehr-worktrees/grpo-run")
REPO = Path("/home/profsynapse/code/Epistemic-Humility-Research")
EVAL = REPO / "archive/experiment/phase1/eval"

METRICS = [
    "truthful_pct",
    "refusal_recall_pct",
    "answer_on_unknown_pct",
    "over_refusal_pct",
    "correct_on_known_pct",
    "refusal_rate_pct",
]

# GRPO-touching arms (Matrix table, AMENDMENT.md:123-134): every arm whose
# lineage includes a GRPO stage. clean_sft, clean_sft_dpo, clean_sft_kto are
# NOT GRPO-touching and excluded by the G3 spec ("every GRPO-touching arm").
ARMS_SEED23 = {
    "clean_sft_grpo_v2": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed2_full_4b/clean_schema_sft_grpo_v2_seed2__selfaware/metrics.json",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_v2_seed3_full_4b/clean_schema_sft_grpo_v2_seed3__selfaware/metrics.json",
    },
    "clean_sft_dpo_grpo": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_grpo_seed2_full_4b/clean_sft_dpo_grpo_seed2__selfaware/metrics.json",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_dpo_grpo_seed3_full_4b/clean_sft_dpo_grpo_seed3__selfaware/metrics.json",
    },
    "clean_sft_kto_grpo": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_kto_grpo_seed2_full_4b/clean_sft_kto_grpo_seed2__selfaware/metrics.json",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_kto_grpo_seed3_full_4b/clean_sft_kto_grpo_seed3__selfaware/metrics.json",
    },
    "clean_sft_grpo_dpo": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_dpo_seed2_full_4b/clean_sft_grpo_dpo_seed2__selfaware/metrics.json",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_dpo_seed3_full_4b/clean_sft_grpo_dpo_seed3__selfaware/metrics.json",
    },
    "clean_sft_grpo_kto": {
        2: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_kto_seed2_full_4b/clean_sft_grpo_kto_seed2__selfaware/metrics.json",
        3: "results_grpo3seed_response_confidence_selfaware_clean_sft_grpo_kto_seed3_full_4b/clean_sft_grpo_kto_seed3__selfaware/metrics.json",
    },
}

SEED1_CSV = REPO / "archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv"


def load_seed23():
    data = {}
    flags = []
    for arm, seeds in ARMS_SEED23.items():
        data[arm] = {}
        for seed, rel in seeds.items():
            p = EVAL / rel
            if not p.exists():
                flags.append(f"MISSING metrics.json: arm={arm} seed={seed} path={p}")
                continue
            d = json.loads(p.read_text())
            n = d["metrics"]["n"]
            if n != 3369:
                flags.append(f"N MISMATCH: arm={arm} seed={seed} n={n} (expected 3369) path={p}")
            row = {m: d["metrics"][m] for m in METRICS}
            row["_path"] = str(p.relative_to(REPO))
            row["_n"] = n
            row["_counts"] = d.get("counts", {})
            data[arm][seed] = row
    return data, flags


def load_seed1():
    rows = {}
    with open(SEED1_CSV) as f:
        for r in csv.DictReader(f):
            arm = r["normalized_arm"]
            if arm in ARMS_SEED23:
                rows[arm] = {
                    "truthful_pct": float(r["mean_truthful_pct"]),
                    "refusal_recall_pct": float(r["mean_refusal_recall_pct"]),
                    "answer_on_unknown_pct": float(r["mean_answer_on_unknown_pct"]),
                    "over_refusal_pct": float(r["mean_over_refusal_pct"]),
                    "correct_on_known_pct": float(r["mean_correct_on_known_pct"]),
                    "refusal_rate_pct": float(r["mean_refusal_rate_pct"]),
                    "_source_metrics_referenced": r["source_metrics"],
                    "_n_runs": r["n_runs"],
                }
    return rows


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


def main():
    seed23, flags = load_seed23()
    seed1 = load_seed1()

    print("=" * 100)
    print("PER-SEED TABLE (GRPO-touching arms x metric x seed)")
    print("=" * 100)
    for arm in ARMS_SEED23:
        print(f"\n[{arm}]")
        s1 = seed1.get(arm, {})
        for m in METRICS:
            v1 = s1.get(m)
            v2 = seed23.get(arm, {}).get(2, {}).get(m)
            v3 = seed23.get(arm, {}).get(3, {}).get(m)
            print(f"  {m:24s} seed1={v1!s:>8} seed2={v2!s:>8} seed3={v3!s:>8}")

    print("\n" + "=" * 100)
    print("THREE-SEED MEAN + 95% BOOTSTRAP CI (seed-level resample, n_resamples=10000, seed=12345)")
    print("=" * 100)
    for arm in ARMS_SEED23:
        print(f"\n[{arm}]")
        s1 = seed1.get(arm, {})
        for m in METRICS:
            v1 = s1.get(m)
            v2 = seed23.get(arm, {}).get(2, {}).get(m)
            v3 = seed23.get(arm, {}).get(3, {}).get(m)
            if v1 is None or v2 is None or v3 is None:
                print(f"  {m:24s} INCOMPLETE (missing a seed value)")
                continue
            vals = [v1, v2, v3]
            mean = sum(vals) / 3
            lo, hi = bootstrap_ci(vals)
            print(f"  {m:24s} mean={mean:7.3f}  95% CI=[{lo:7.3f}, {hi:7.3f}]  values={vals}")

    print("\n" + "=" * 100)
    print("ARTIFACT PATHS READ (seed 2 / seed 3)")
    print("=" * 100)
    for arm, seeds in seed23.items():
        for seed, row in seeds.items():
            print(f"  arm={arm} seed={seed} n={row['_n']} path={row['_path']}")
            print(f"    counts={row['_counts']}")

    print("\n" + "=" * 100)
    print(f"SEED-1 SOURCE: {SEED1_CSV.relative_to(REPO)}  (n_runs=1 rows; underlying per-seed")
    print("metrics.json referenced by this CSV's source_metrics column is NOT present on disk")
    print("in this checkout -- git ls-files and git log --all --diff-filter=A both empty for")
    print("those paths. correct_on_known_pct raw counts are unavailable for seed 1 for this reason.")
    print("=" * 100)
    for arm, row in seed1.items():
        print(f"  arm={arm} referenced_source={row['_source_metrics_referenced']} n_runs={row['_n_runs']}")

    if flags:
        print("\n" + "=" * 100)
        print("FLAGS")
        print("=" * 100)
        for f in flags:
            print(f"  {f}")
    else:
        print("\nNo missing-artifact or n-mismatch flags for seed 2/3.")


if __name__ == "__main__":
    main()
