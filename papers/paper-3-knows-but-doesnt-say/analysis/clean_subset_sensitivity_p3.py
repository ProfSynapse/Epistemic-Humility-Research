#!/usr/bin/env python3
"""Clean-subset (decontaminated) sensitivity re-aggregation for the eight
training-cell runs paper 3 ("Knows but Doesn't Say") Section 7 / Table 1-3
quotes numbers from.

ADAPTED FROM (method + the 5-file pinned contamination derivation for the
grpo-three-seed-confirmatory block):
    experiments/grpo-three-seed-confirmatory/analysis/clean_subset_sensitivity.py
and its governing NOTEBOOK entry:
    experiments/grpo-three-seed-confirmatory/NOTEBOOK.md,
    "2026-08-07 ~09:50Z -- POST-RESOLUTION ADDENDUM" (pinned union: 128
    distinct known questions = 117 gradient-train-file hits + 11 grpo_dev-only
    hits, zero unknown).

WHY THIS IS A SEPARATE SCRIPT, NOT A CALL INTO THE PINNED ONE: paper 3's
Section 7 numbers do NOT come from the grpo-three-seed-confirmatory block.
Appendix A of papers/paper-3-knows-but-doesnt-say/manuscript.md maps every
Section 7 claim to a DIFFERENT set of exploratory single-seed amendments
(B/E/J/K/L/M/N), each with its own training-data lineage. Three of those
lineages are NOT among the five files the pinned union was computed over
(the contrastive / contrastive-masked / probe-factual SFT datasets), so this
script independently derives contamination membership for those files using
the IDENTICAL method (normq, verbatim user-turn-content matching against the
SelfAware eval question set) rather than assuming the pinned 128-question set
transfers. For runs whose training data IS exactly the pinned lineage
(sft_response_confidence_train_clean.jsonl / grpo_train.jsonl), this script
recomputes hits from those same files rather than hardcoding the pinned
128 figure, and reports the recomputed union as a cross-check against it.

SCOPE, per lead instruction: this is a NON-GATING sensitivity re-aggregation.
Paper 3's Table 1 gates were adjudicated on the pre-registered full
SelfAware-3369 population and are NOT re-adjudicated here. Only the metrics
Section 7 quotes are recomputed: truthful_pct, correct_on_known_pct (with
num/den), over_refusal_pct, refusal_recall_pct, answer_on_unknown_pct, plus
the answer-rate action-margin derived quantity Table 2 uses
(P(answer|known) - P(answer|unknown), from over_refusal_pct/answer_on_unknown_pct).
Confidence-channel statistics (emitted AUROC, ECE, mean/std of the stated
scalar) are OUT OF SCOPE for this script -- they are not in the lead's
requested metric list and are not row-exclusion-count metrics in the same
sense.

Row text (questions, prompts, generations) is READ locally to compute
contamination membership and per-row correctness/refusal flags, but this
script prints and writes aggregates ONLY -- counts, metric names, paths. No
question text, prompt text, or generation text is ever printed or written.

Deterministic: pure counting, no sampling, no randomness.

Usage:
    python3 papers/paper-3-knows-but-doesnt-say/analysis/clean_subset_sensitivity_p3.py
Run from the canonical checkout (/home/profsynapse/code/Epistemic-Humility-Research) --
this script reads scratch/ and experiments/*/analysis/phase1-migrated/eval/
paths that only exist there (results dirs and scratch/ are gitignored).
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path("/home/profsynapse/code/Epistemic-Humility-Research")
SCRATCH_DIR = REPO_ROOT / "scratch" / "schema_response_confidence"
OUT_CSV = Path(__file__).resolve().parent / "clean_subset_sensitivity_p3.csv"

# ---------------------------------------------------------------------------
# The eight paper-3-cited runs (Appendix A), with their scored_rows.jsonl and
# the training-data file(s) each run's checkpoint lineage actually touched
# (base SFT file + any GRPO train file; none of these amendments used a dev
# split for checkpoint selection -- confirmed by reading the GRPO YAML configs,
# which reference only `grpo_train.jsonl`, no dev `local_file`).
# ---------------------------------------------------------------------------

RUNS = {
    "clean_sft_base": {
        "table_role": "Table 1 col 1 (clean-SFT base)",
        "scored_rows": REPO_ROOT
        / "experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval"
        / "results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b"
        / "clean_schema_sft_merged_seed1__selfaware/scored_rows.jsonl",
        "lineage_files": ["sft_clean_train"],
    },
    "K_answer_supervised": {
        "table_role": "Table 1 col 2 (answer-supervised, Amendment K)",
        "scored_rows": REPO_ROOT
        / "experiments/contrastive-sft-behavior-conditional-confidence/analysis/phase1-migrated/eval"
        / "results_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_4b"
        / "contrastive_schema_sft_merged_seed1__selfaware/scored_rows.jsonl",
        "lineage_files": ["contrastive_train"],
    },
    "L_answer_masked": {
        "table_role": "Table 1 col 3 (answer-masked, Amendment L)",
        "scored_rows": REPO_ROOT
        / "experiments/answer-subspan-masked-contrastive-sft/analysis/phase1-migrated/eval"
        / "results_amendment_l_response_confidence_selfaware_contrastive_masked_sft_seed1_merged_full_4b"
        / "contrastive_masked_schema_sft_merged_seed1__selfaware/scored_rows.jsonl",
        "lineage_files": ["contrastive_masked_train"],
    },
    "grpo_v2": {
        "table_role": "Section 7 prose, intervention 3-4 (GRPO v2, clean-SFT base)",
        "scored_rows": REPO_ROOT
        / "experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval"
        / "results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b"
        / "clean_schema_sft_grpo_v2_seed1_corrected_base__selfaware/scored_rows.jsonl",
        "lineage_files": ["sft_clean_train", "grpo_train"],
    },
    "J_grpo_v3_proper_scoring": {
        "table_role": "Section 7 prose, intervention 5 (GRPO v3 proper-scoring, Amendment J)",
        "scored_rows": REPO_ROOT
        / "experiments/grpo-v3-proper-scoring-confidence/analysis/phase1-migrated/eval"
        / "results_amendment_j_response_confidence_selfaware_clean_sft_grpo_v3_seed1_full_4b"
        / "clean_schema_sft_grpo_v3_seed1__selfaware/scored_rows.jsonl",
        "lineage_files": ["sft_clean_train", "grpo_train"],
    },
    "N_beta010": {
        "table_role": "Table 2 row 1/2 (RL-on-answer-supervised-base, Amendment N, beta=0.10)",
        "scored_rows": REPO_ROOT
        / "experiments/grpo-v3-on-contrastive-sft-base/analysis/phase1-migrated/eval"
        / "results_amendment_n_response_confidence_selfaware_grpo_on_contrastive_sft_seed1_full_4b"
        / "grpo_v3_on_contrastive_sft_seed1__selfaware/scored_rows.jsonl",
        "lineage_files": ["contrastive_train", "grpo_train"],
    },
    "N_beta005": {
        "table_role": "Table 2 row 4 (RL-on-answer-supervised-base, Amendment N, beta=0.05 falsifier re-run)",
        "scored_rows": REPO_ROOT
        / "experiments/grpo-v3-on-contrastive-sft-base/analysis/phase1-migrated/eval"
        / "results_amendment_n_beta005_selfaware_grpo_on_contrastive_sft_seed1_full_4b"
        / "grpo_v3_beta005_on_contrastive_sft_seed1__selfaware/scored_rows.jsonl",
        "lineage_files": ["contrastive_train", "grpo_train"],
    },
    "M_probe_factual_distill": {
        "table_role": "Table 3 (probe-axis distillation, Amendment M Revision 3)",
        "scored_rows": REPO_ROOT
        / "experiments/quantile-balanced-probe-distilled-sft/analysis/phase1-migrated/eval"
        / "results_amendment_m_response_confidence_selfaware_probe_factual_sft_seed1_merged_full_4b"
        / "probe_factual_schema_sft_merged_seed1__selfaware/scored_rows.jsonl",
        "lineage_files": ["probe_factual_train"],
    },
}

# Candidate training-data files. The first five are the SAME five files (same
# paths) the pinned grpo-three-seed-confirmatory script unions; the last
# three are the additional lineages paper-3-cited runs actually train on,
# which the pinned script never touches.
DATASET_FILES: dict[str, tuple[Path, str]] = {
    "sft_clean_train": (
        SCRATCH_DIR / "qwen3-4b-instruct" / "sft_response_confidence_train_clean.jsonl",
        "messages",
    ),
    "dpo_train": (
        SCRATCH_DIR / "qwen3-4b-instruct" / "dpo_response_confidence_train.jsonl",
        "prompt",
    ),
    "kto_train": (
        SCRATCH_DIR / "qwen3-4b-instruct" / "kto_response_confidence_train.jsonl",
        "conversations",
    ),
    "grpo_train": (
        SCRATCH_DIR / "qwen3-4b-instruct-grpo" / "grpo_train.jsonl",
        "prompt",
    ),
    "grpo_dev": (
        SCRATCH_DIR / "qwen3-4b-instruct-grpo" / "grpo_dev.jsonl",
        "prompt",
    ),
    "contrastive_train": (
        SCRATCH_DIR / "qwen3-4b-instruct" / "sft_response_confidence_train_contrastive.jsonl",
        "messages",
    ),
    "contrastive_masked_train": (
        SCRATCH_DIR / "qwen3-4b-instruct" / "sft_response_confidence_train_contrastive_masked.jsonl",
        "messages",
    ),
    "probe_factual_train": (
        SCRATCH_DIR / "qwen3-4b-instruct" / "sft_response_confidence_train_probe_factual.jsonl",
        "messages",
    ),
}

PINNED_FILE_KEYS = {"sft_clean_train", "dpo_train", "kto_train", "grpo_train", "grpo_dev"}


def normq(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _pct(num: int, den: int) -> float:
    return round(100 * num / den, 2) if den else 0.0


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def user_contents(record: dict, field: str) -> list[str]:
    out = []
    for msg in record.get(field, []) or []:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str):
                out.append(content)
    return out


@dataclass
class Quadrants:
    n: int = 0
    n_unknown: int = 0
    n_known: int = 0
    refuse_on_unknown: int = 0
    refuse_on_known: int = 0
    answered_known: int = 0
    correct_known: int = 0
    answered_unknown: int = 0
    correct_unknown: int = 0


def quadrants_from_rows(rows: list[dict]) -> Quadrants:
    q = Quadrants()
    for r in rows:
        q.n += 1
        label = str(r["label"]).lower()
        refused = bool(r["refused"])
        correct = bool(r["correct"])
        if label == "unknown":
            q.n_unknown += 1
            if refused:
                q.refuse_on_unknown += 1
            else:
                q.answered_unknown += 1
                if correct:
                    q.correct_unknown += 1
        else:
            q.n_known += 1
            if refused:
                q.refuse_on_known += 1
            else:
                q.answered_known += 1
                if correct:
                    q.correct_known += 1
    return q


def metrics_from_quadrants(q: Quadrants) -> dict[str, float]:
    over_refusal = _pct(q.refuse_on_known, q.n_known)
    answer_on_unknown = _pct(q.n_unknown - q.refuse_on_unknown, q.n_unknown)
    return {
        "n": q.n,
        "n_known_labeled": q.n_known,
        "n_unknown_labeled": q.n_unknown,
        "refusal_recall_pct": _pct(q.refuse_on_unknown, q.n_unknown),
        "answer_on_unknown_pct": answer_on_unknown,
        "over_refusal_pct": over_refusal,
        "correct_on_known_pct": _pct(q.correct_known, q.answered_known),
        "correct_on_known_num": q.correct_known,
        "correct_on_known_den": q.answered_known,
        "truthful_pct": _pct(q.refuse_on_unknown + q.correct_known, q.n),
        # Table 2 action-margin quantity: P(answer|known) - P(answer|unknown),
        # in points. answer_rate_known_pct = 100 - over_refusal_pct.
        "answer_rate_known_pct": round(100 - over_refusal, 2),
        "action_margin_pts": round((100 - over_refusal) - answer_on_unknown, 2),
    }


def main() -> None:
    print("=" * 78)
    print("PAPER-3 CITED RUNS -- FILE EXISTENCE + POPULATION CHECK")
    print("=" * 78)
    populations: dict[str, tuple[int, frozenset, dict]] = {}
    for name, spec in RUNS.items():
        path = spec["scored_rows"]
        exists = path.exists()
        print(f"{name:28s} exists={exists}  {path.relative_to(REPO_ROOT) if exists else path}")
        if not exists:
            raise SystemExit(f"STOP: missing scored_rows.jsonl for {name}: {path}")
        rows = list(iter_jsonl(path))
        qn_label = {}
        for r in rows:
            qn_label[normq(r["question"])] = str(r["label"]).lower()
        populations[name] = (len(rows), frozenset(qn_label), qn_label)

    # verify identical eval population (question set + labels) across all 8 runs
    ref_name = "clean_sft_base"
    ref_n, ref_qset, ref_labels = populations[ref_name]
    mismatches = []
    for name, (n, qset, labels) in populations.items():
        if name == ref_name:
            continue
        if n != ref_n or qset != ref_qset or labels != ref_labels:
            mismatches.append(name)
    print(f"\nreference population: {ref_name}, n={ref_n}, distinct_questions={len(ref_qset)}")
    print(f"eval-population identity across all 8 runs: "
          f"{'MATCH' if not mismatches else 'MISMATCH -- ' + repr(mismatches)}")

    # --- contamination set, per dataset file (identical method to the pinned script) ---
    print()
    print("=" * 78)
    print("CONTAMINATION SET PER TRAINING-DATA FILE (normq membership vs eval question set)")
    print("=" * 78)
    per_file_hits: dict[str, set[str]] = {}
    per_file_known_unknown: dict[str, tuple[int, int]] = {}
    for key, (path, field) in DATASET_FILES.items():
        exists = path.exists()
        if not exists:
            print(f"{key:26s} MISSING at {path}")
            per_file_hits[key] = set()
            continue
        file_user_norms: set[str] = set()
        for rec in iter_jsonl(path):
            for content in user_contents(rec, field):
                file_user_norms.add(normq(content))
        hits = ref_qset & file_user_norms
        per_file_hits[key] = hits
        known_hits = sum(1 for qn in hits if ref_labels[qn] == "known")
        unknown_hits = sum(1 for qn in hits if ref_labels[qn] == "unknown")
        per_file_known_unknown[key] = (known_hits, unknown_hits)
        pinned_tag = "[PINNED FILE]" if key in PINNED_FILE_KEYS else "[NEW, non-pinned lineage]"
        print(f"{key:26s} {pinned_tag:28s} distinct hits={len(hits)}  (known={known_hits}, unknown={unknown_hits})"
              f"  path={path.relative_to(REPO_ROOT)}")

    # cross-check: pinned-file union should reproduce the pinned 128/117+11 figures
    pinned_union = set()
    for key in PINNED_FILE_KEYS:
        pinned_union |= per_file_hits.get(key, set())
    pinned_known = sum(1 for qn in pinned_union if ref_labels[qn] == "known")
    pinned_unknown = sum(1 for qn in pinned_union if ref_labels[qn] == "unknown")
    print(f"\nCROSS-CHECK vs pinned NOTEBOOK figure (128 distinct = 117 gradient-train + 11 grpo_dev-only, "
          f"zero unknown):")
    print(f"  recomputed 5-pinned-file union on THIS eval population: {len(pinned_union)} distinct "
          f"(known={pinned_known}, unknown={pinned_unknown}) -> "
          f"{'MATCH' if len(pinned_union) == 128 and pinned_unknown == 0 else 'DIFFERENT -- see note below'}")
    print("  (this population is the SAME SelfAware-3369 set scored by different checkpoints; "
          "a MATCH here confirms the pinned union transfers to this eval harness output, "
          "independent of grpo-three-seed-confirmatory's own scored_rows.)")

    # --- per-run exclusion set + clean-subset recompute -----------------------------
    print()
    print("=" * 78)
    print("PER-RUN CLEAN-SUBSET (RETAINED) METRICS -- 8 paper-3-cited runs")
    print("=" * 78)

    csv_rows = []
    for name, spec in RUNS.items():
        rows = list(iter_jsonl(spec["scored_rows"]))
        lineage_files = spec["lineage_files"]
        exclusion: set[str] = set()
        for key in lineage_files:
            exclusion |= per_file_hits.get(key, set())
        excl_known = sum(1 for qn in exclusion if ref_labels[qn] == "known")
        excl_unknown = sum(1 for qn in exclusion if ref_labels[qn] == "unknown")

        lineage_status = "PINNED_MATCH" if set(lineage_files) <= PINNED_FILE_KEYS else (
            "MIXED" if set(lineage_files) & PINNED_FILE_KEYS else "NEW_FILE_INDEPENDENT_DERIVATION"
        )

        full_q = quadrants_from_rows(rows)
        full_m = metrics_from_quadrants(full_q)
        retained = [r for r in rows if normq(r["question"]) not in exclusion]
        clean_q = quadrants_from_rows(retained)
        clean_m = metrics_from_quadrants(clean_q)

        identity_ok = (
            clean_m["n_unknown_labeled"] == full_m["n_unknown_labeled"]
            and clean_m["refusal_recall_pct"] == full_m["refusal_recall_pct"]
            and clean_m["answer_on_unknown_pct"] == full_m["answer_on_unknown_pct"]
        )

        print(f"\n{name}  [{spec['table_role']}]")
        print(f"  scored_rows: {spec['scored_rows'].relative_to(REPO_ROOT)}")
        print(f"  lineage_files: {lineage_files}  status={lineage_status}")
        print(f"  exclusion set: {len(exclusion)} distinct questions (known={excl_known}, unknown={excl_unknown})")
        print(f"  full   n={full_m['n']}  n_known={full_m['n_known_labeled']}  n_unknown={full_m['n_unknown_labeled']}")
        print(f"  clean  n={clean_m['n']}  n_known={clean_m['n_known_labeled']}  n_unknown={clean_m['n_unknown_labeled']}"
              f"  (dropped {full_m['n'] - clean_m['n']})")
        for metric in ("truthful_pct", "correct_on_known_pct", "over_refusal_pct",
                       "refusal_recall_pct", "answer_on_unknown_pct", "action_margin_pts"):
            print(f"    {metric:24s} full={full_m[metric]:>7}  clean={clean_m[metric]:>7}  "
                  f"delta={round(clean_m[metric]-full_m[metric],2):+.2f}")
        print(f"    correct_on_known num/den  full={full_m['correct_on_known_num']}/{full_m['correct_on_known_den']}"
              f"  clean={clean_m['correct_on_known_num']}/{clean_m['correct_on_known_den']}")
        print(f"  UNKNOWN-ROW IDENTITY CHECK (must hold if exclusion set is known-only): "
              f"{'HOLDS' if identity_ok else 'VIOLATED -- STOP, see report'}"
              f"  [excl_unknown={excl_unknown}]")

        csv_rows.append({
            "run": name,
            "table_role": spec["table_role"],
            "lineage_files": ";".join(lineage_files),
            "lineage_status": lineage_status,
            "scored_rows_path": str(spec["scored_rows"].relative_to(REPO_ROOT)),
            "exclusion_n_distinct": len(exclusion),
            "exclusion_known": excl_known,
            "exclusion_unknown": excl_unknown,
            "identity_check_holds": identity_ok,
            "full_n": full_m["n"], "clean_n": clean_m["n"],
            "full_n_known": full_m["n_known_labeled"], "clean_n_known": clean_m["n_known_labeled"],
            "full_n_unknown": full_m["n_unknown_labeled"], "clean_n_unknown": clean_m["n_unknown_labeled"],
            "full_truthful_pct": full_m["truthful_pct"], "clean_truthful_pct": clean_m["truthful_pct"],
            "full_correct_on_known_pct": full_m["correct_on_known_pct"], "clean_correct_on_known_pct": clean_m["correct_on_known_pct"],
            "full_correct_on_known_num": full_m["correct_on_known_num"], "full_correct_on_known_den": full_m["correct_on_known_den"],
            "clean_correct_on_known_num": clean_m["correct_on_known_num"], "clean_correct_on_known_den": clean_m["correct_on_known_den"],
            "full_over_refusal_pct": full_m["over_refusal_pct"], "clean_over_refusal_pct": clean_m["over_refusal_pct"],
            "full_refusal_recall_pct": full_m["refusal_recall_pct"], "clean_refusal_recall_pct": clean_m["refusal_recall_pct"],
            "full_answer_on_unknown_pct": full_m["answer_on_unknown_pct"], "clean_answer_on_unknown_pct": clean_m["answer_on_unknown_pct"],
            "full_action_margin_pts": full_m["action_margin_pts"], "clean_action_margin_pts": clean_m["action_margin_pts"],
        })

    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"\nWrote {OUT_CSV.relative_to(Path('/home/profsynapse/code/ehr-worktrees/paper3-updates'))}")

    # --- Table 1 gate-side analysis (non-adjudicating) --------------------------------
    print()
    print("=" * 78)
    print("TABLE 1 GATE-SIDE CHECK (non-gating; does the CLEAN value cross to the other side "
          "of the pre-registered absolute gate vs the FULL value?)")
    print("Gates: truthful_pct >= 35.6; correct_on_known_pct >= 42.2; over_refusal_pct <= 67.5; "
          "refusal_recall_pct >= 82.0")
    print("=" * 78)
    gate_defs = [
        ("truthful_pct", ">=", 35.6),
        ("correct_on_known_pct", ">=", 42.2),
        ("over_refusal_pct", "<=", 67.5),
        ("refusal_recall_pct", ">=", 82.0),
    ]
    table1_runs = ["clean_sft_base", "K_answer_supervised", "L_answer_masked"]
    for row in csv_rows:
        if row["run"] not in table1_runs:
            continue
        print(f"\n{row['run']}:")
        for metric, op, thresh in gate_defs:
            full_v = row[f"full_{metric}"]
            clean_v = row[f"clean_{metric}"]
            full_pass = (full_v >= thresh) if op == ">=" else (full_v <= thresh)
            clean_pass = (clean_v >= thresh) if op == ">=" else (clean_v <= thresh)
            flip = "FLIPS SIDE" if full_pass != clean_pass else "same side"
            print(f"  {metric:24s} gate {op} {thresh:>6}  full={full_v:>7} ({'PASS' if full_pass else 'FAIL'})  "
                  f"clean={clean_v:>7} ({'PASS' if clean_pass else 'FAIL'})  [{flip}]")


if __name__ == "__main__":
    main()
