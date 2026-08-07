#!/usr/bin/env python3
"""Clean-subset (decontaminated) sensitivity re-aggregation for the
`grpo-three-seed-confirmatory` block.

CONTEXT: a red-team pass (NOTEBOOK.md, 2026-08-07 "RED-TEAM PASS COMPLETE"
entry) found 117 distinct SelfAware eval questions appearing verbatim as
user-role training prompts across this block's datasets. This script
independently re-derives that contamination set and recomputes all headline
eval metrics over the DECONTAMINATED (retained) subset of the eval
population, for every seed-2/seed-3 full-eval run in the block.

NOTHING computed here changes any gate verdict. Gates were pre-registered
and adjudicated on the full SelfAware-3369 population (gates.yaml, pinned).
This is a non-gating sensitivity table for paper-2 reporting only.

Row text (questions, prompts, generations) is READ locally to compute
contamination membership and per-row correctness/refusal flags, but this
script prints and returns aggregates ONLY -- counts, metric names, paths.
No question text, prompt text, or generation text is ever printed or written
by this script. The repo is public; keep it that way.

Deterministic: pure counting, no sampling, no randomness.

Usage:
    python3 experiments/grpo-three-seed-confirmatory/analysis/clean_subset_sensitivity.py
Run from the canonical checkout (/home/profsynapse/code/Epistemic-Humility-Research).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_DIR = REPO_ROOT / "archive" / "experiment" / "phase1" / "eval"
SCRATCH_DIR = REPO_ROOT / "scratch" / "schema_response_confidence"

# The block's 8 cell ids (cell.yaml), each run at seeds 2 and 3 -> 16 full evals.
CELL_IDS = [
    "clean_sft",
    "clean_sft_dpo",
    "clean_sft_kto",
    "clean_sft_grpo_v2",
    "clean_sft_dpo_grpo",
    "clean_sft_kto_grpo",
    "clean_sft_grpo_dpo",
    "clean_sft_grpo_kto",
]
SEEDS = [2, 3]

# Dataset files this block's cells consume (cell.yaml "datasets", plus the
# GRPO dev file per the lead's instruction). (label, path, list_field_name).
DATASET_FILES: list[tuple[str, Path, str]] = [
    ("sft_clean_train", SCRATCH_DIR / "qwen3-4b-instruct" / "sft_response_confidence_train_clean.jsonl", "messages"),
    ("dpo_train", SCRATCH_DIR / "qwen3-4b-instruct" / "dpo_response_confidence_train.jsonl", "prompt"),
    ("kto_train", SCRATCH_DIR / "qwen3-4b-instruct" / "kto_response_confidence_train.jsonl", "conversations"),
    ("grpo_train", SCRATCH_DIR / "qwen3-4b-instruct-grpo" / "grpo_train.jsonl", "prompt"),
    ("grpo_dev", SCRATCH_DIR / "qwen3-4b-instruct-grpo" / "grpo_dev.jsonl", "prompt"),
]

# Canonical eval population source: any one full-eval scored_rows.jsonl (the
# eval population -- selfaware-full-3369 -- is fixed across all 16 runs; this
# choice is verified, not assumed, in main()).
CANONICAL_RUN = ("clean_sft_grpo_v2", 3)


# ---------------------------------------------------------------------------
# Normalization: lowercase, whitespace-collapsed, stripped. Deliberately NOT
# scorers.norm_question (which also strips an HIR confidence-prefix that does
# not occur in this block's plain schema prompts) -- this matches the lead's
# stated method exactly, for cross-check against the 117-distinct finding.
# ---------------------------------------------------------------------------
def normq(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _pct(num: int, den: int) -> float:
    """Verbatim from archive/experiment/phase1/eval/scorers.py:_pct."""
    return round(100 * num / den, 2) if den else 0.0


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def user_contents(record: dict, field: str) -> list[str]:
    """All role=='user' message contents in a chat-format record field."""
    out = []
    for msg in record.get(field, []) or []:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str):
                out.append(content)
    return out


def discover_runs() -> dict[tuple[str, int], Path]:
    """Map (cell_id, seed) -> scored_rows.jsonl path for the 16 full evals."""
    runs: dict[tuple[str, int], Path] = {}
    candidates = sorted(EVAL_DIR.glob("results_grpo3seed_*_full_4b"))
    for d in candidates:
        name = d.name
        seed = None
        for s in SEEDS:
            if f"_seed{s}_" in name:
                seed = s
                break
        if seed is None:
            continue
        cell_id = None
        for cid in CELL_IDS:
            # dir names embed the cell id around the seed marker, e.g.
            # results_grpo3seed_..._clean_sft_grpo_v2_seed3_full_4b or
            # results_grpo3seed_..._clean_sft_seed3_merged_full_4b (stage-1).
            if f"_{cid}_seed{seed}_" in name or f"_{cid}_seed{seed}_merged_" in name:
                if cell_id is None or len(cid) > len(cell_id):
                    cell_id = cid
        if cell_id is None:
            continue
        scored = list(d.glob("*/scored_rows.jsonl"))
        if len(scored) != 1:
            raise SystemExit(f"expected exactly one scored_rows.jsonl under {d}, found {len(scored)}")
        runs[(cell_id, seed)] = scored[0]
    return runs


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
    """Mirrors scorers.score_quadrants / metrics_from_quadrants (scorers.py:
    194-289) exactly, but consumes the already-scored 'label'/'refused'/
    'correct' fields written by run_eval.py's _scored_row_payload (run_eval.py
    :531-556), which computes them via this identical formula
    (label_from_target=False for the selfaware in-domain eval set). Reading
    the precomputed fields, rather than re-parsing generated_answer, is
    provenance-exact for this population: the fields ARE the scorer output.
    """
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
    return {
        "n": q.n,
        "n_unknown_labeled": q.n_unknown,
        "n_known_labeled": q.n_known,
        "refusal_recall_pct": _pct(q.refuse_on_unknown, q.n_unknown),
        "answer_on_unknown_pct": _pct(q.n_unknown - q.refuse_on_unknown, q.n_unknown),
        "over_refusal_pct": _pct(q.refuse_on_known, q.n_known),
        "refusal_rate_pct": _pct(q.refuse_on_unknown + q.refuse_on_known, q.n),
        "correct_on_known_pct": _pct(q.correct_known, q.answered_known),
        "correct_on_known_num": q.correct_known,
        "correct_on_known_den": q.answered_known,
        "truthful_pct": _pct(q.refuse_on_unknown + q.correct_known, q.n),
    }


def main() -> None:
    runs = discover_runs()
    assert len(runs) == 16, f"expected 16 full-eval runs, found {len(runs)}: {sorted(runs)}"
    for cid in CELL_IDS:
        for seed in SEEDS:
            assert (cid, seed) in runs, f"missing run for {cid} seed {seed}"

    # --- canonical eval population -----------------------------------
    canon_path = runs[CANONICAL_RUN]
    canon_rows = list(iter_jsonl(canon_path))
    eval_qnorm_label: dict[str, str] = {}
    conflicts = 0
    for r in canon_rows:
        qn = normq(r["question"])
        lab = str(r["label"]).lower()
        if qn in eval_qnorm_label and eval_qnorm_label[qn] != lab:
            conflicts += 1
        eval_qnorm_label[qn] = lab
    eval_qnorms = set(eval_qnorm_label)

    print("=" * 78)
    print("CANONICAL EVAL POPULATION")
    print("=" * 78)
    print(f"source: {canon_path.relative_to(REPO_ROOT)}")
    print(f"rows: {len(canon_rows)}  distinct normalized questions: {len(eval_qnorms)}"
          f"  label-conflicting normalized questions: {conflicts}")

    # verify every other run shares the same eval population (question set + labels)
    pop_mismatches = []
    for (cid, seed), path in runs.items():
        if (cid, seed) == CANONICAL_RUN:
            continue
        rows = list(iter_jsonl(path))
        qn_label = {}
        for r in rows:
            qn_label[normq(r["question"])] = str(r["label"]).lower()
        if len(rows) != len(canon_rows) or set(qn_label) != eval_qnorms:
            pop_mismatches.append((cid, seed, len(rows), len(qn_label)))
    print(f"eval-population identity across all 16 runs: "
          f"{'MATCH' if not pop_mismatches else 'MISMATCH -- ' + repr(pop_mismatches)}")

    # --- contamination set, per file -----------------------------------
    print()
    print("=" * 78)
    print("CONTAMINATION SET (normalized eval question membership in training user turns)")
    print("=" * 78)
    per_file_hits: dict[str, set[str]] = {}
    for label, path, field in DATASET_FILES:
        if not path.exists():
            print(f"{label}: MISSING at {path.relative_to(REPO_ROOT)}")
            per_file_hits[label] = set()
            continue
        file_user_norms: set[str] = set()
        for rec in iter_jsonl(path):
            for content in user_contents(rec, field):
                file_user_norms.add(normq(content))
        hits = eval_qnorms & file_user_norms
        per_file_hits[label] = hits
        print(f"{label:20s} path={path.relative_to(REPO_ROOT)}")
        print(f"{'':20s} distinct contaminated eval questions: {len(hits)}")

    union_qnorms: set[str] = set()
    for hits in per_file_hits.values():
        union_qnorms |= hits
    union_labels = {eval_qnorm_label[qn] for qn in union_qnorms}
    known_count = sum(1 for qn in union_qnorms if eval_qnorm_label[qn] == "known")
    unknown_count = sum(1 for qn in union_qnorms if eval_qnorm_label[qn] == "unknown")

    print()
    print(f"UNION distinct contaminated eval questions: {len(union_qnorms)}"
          f"  (known={known_count}, unknown={unknown_count}, labels_present={sorted(union_labels)})")

    contaminated_rows = [r for r in canon_rows if normq(r["question"]) in union_qnorms]
    contaminated_rows_known = sum(1 for r in contaminated_rows if str(r["label"]).lower() == "known")
    contaminated_rows_unknown = sum(1 for r in contaminated_rows if str(r["label"]).lower() == "unknown")
    print(f"UNION contaminated EVAL ROW count (canonical population, n={len(canon_rows)}): "
          f"{len(contaminated_rows)}  (known={contaminated_rows_known}, unknown={contaminated_rows_unknown})")

    print()
    print("CROSS-CHECK against lead's independent finding (117 distinct, all label=known, "
          "118/3369 rows):")
    print(f"  distinct: {len(union_qnorms)} vs 117 -> "
          f"{'MATCH' if len(union_qnorms) == 117 else 'DIFFERENT'}")
    print(f"  rows:     {len(contaminated_rows)} vs 118 -> "
          f"{'MATCH' if len(contaminated_rows) == 118 else 'DIFFERENT'}")
    print(f"  all known, zero unknown: "
          f"{'MATCH' if unknown_count == 0 and known_count == len(union_qnorms) else 'DIFFERENT'}")

    # --- per-run clean-subset recompute -----------------------------------
    print()
    print("=" * 78)
    print("PER-RUN CLEAN-SUBSET (RETAINED) METRICS -- 16 full-eval runs, seeds 2/3")
    print("=" * 78)

    run_metrics: dict[tuple[str, int], dict] = {}
    run_full_metrics: dict[tuple[str, int], dict] = {}
    retained_n_set = set()
    retained_known_unknown_set = set()

    for cid in CELL_IDS:
        for seed in SEEDS:
            path = runs[(cid, seed)]
            rows = list(iter_jsonl(path))
            retained = [r for r in rows if normq(r["question"]) not in union_qnorms]
            q = quadrants_from_rows(retained)
            m = metrics_from_quadrants(q)
            run_metrics[(cid, seed)] = m
            retained_n_set.add(m["n"])
            retained_known_unknown_set.add((m["n_known_labeled"], m["n_unknown_labeled"]))

            metrics_json_path = path.parent / "metrics.json"
            full_m = json.loads(metrics_json_path.read_text())["metrics"]
            run_full_metrics[(cid, seed)] = full_m

            print(f"\n{cid} seed {seed}  ({path.relative_to(REPO_ROOT)})")
            print(f"  retained n={m['n']}  n_known={m['n_known_labeled']}  n_unknown={m['n_unknown_labeled']}"
                  f"  (dropped {len(rows) - len(retained)} of {len(rows)})")
            print(f"  refusal_recall_pct={m['refusal_recall_pct']}  answer_on_unknown_pct={m['answer_on_unknown_pct']}"
                  f"  over_refusal_pct={m['over_refusal_pct']}  refusal_rate_pct={m['refusal_rate_pct']}")
            print(f"  correct_on_known_pct={m['correct_on_known_pct']} "
                  f"(num={m['correct_on_known_num']}, den={m['correct_on_known_den']})"
                  f"  truthful_pct={m['truthful_pct']}")
            # identity check: zero unknown contamination -> unknown-row metrics
            # on the retained subset must exactly equal the full-population ones.
            identity_ok = (
                m["n_unknown_labeled"] == full_m["n_unknown_labeled"]
                and m["refusal_recall_pct"] == full_m["refusal_recall_pct"]
                and m["answer_on_unknown_pct"] == full_m["answer_on_unknown_pct"]
            )
            print(f"  IDENTITY CHECK (unknown-row metrics unchanged vs full population): "
                  f"{'HOLDS' if identity_ok else 'VIOLATED'}"
                  f"  [full n_unknown={full_m['n_unknown_labeled']}, "
                  f"full refusal_recall_pct={full_m['refusal_recall_pct']}, "
                  f"full answer_on_unknown_pct={full_m['answer_on_unknown_pct']}]")

    print()
    print(f"Retained n consistent across all 16 runs: "
          f"{'YES, n=' + str(retained_n_set.pop()) if len(retained_n_set) == 1 else 'NO -- ' + repr(retained_n_set)}")
    print(f"Retained (known, unknown) counts consistent across all 16 runs: "
          f"{'YES, ' + str(retained_known_unknown_set.pop()) if len(retained_known_unknown_set) == 1 else 'NO -- ' + repr(retained_known_unknown_set)}")

    # --- sensitivity deltas: G1-shaped, G2-shaped (non-gating) --------------
    print()
    print("=" * 78)
    print("SENSITIVITY (NON-GATING): G1-shaped (clean_sft_grpo_v2 vs same-seed clean_sft), "
          "clean subset vs full population")
    print("=" * 78)
    for seed in SEEDS:
        clean_m = run_metrics[("clean_sft_grpo_v2", seed)]
        base_m = run_metrics[("clean_sft", seed)]
        full_clean_m = run_full_metrics[("clean_sft_grpo_v2", seed)]
        full_base_m = run_full_metrics[("clean_sft", seed)]
        for metric in ("answer_on_unknown_pct", "refusal_recall_pct"):
            d_clean = round(clean_m[metric] - base_m[metric], 2)
            d_full = round(full_clean_m[metric] - full_base_m[metric], 2)
            print(f"  seed {seed}  {metric}: clean-subset delta {d_clean:+.2f} pp "
                  f"({base_m[metric]} -> {clean_m[metric]})   |   "
                  f"full-population delta {d_full:+.2f} pp ({full_base_m[metric]} -> {full_clean_m[metric]})")

    print()
    print("=" * 78)
    print("SENSITIVITY (NON-GATING): G2-shaped (clean_sft_grpo_dpo vs same-seed clean_sft_grpo_v2), "
          "clean subset vs full population")
    print("=" * 78)
    for seed in SEEDS:
        dpo_m = run_metrics[("clean_sft_grpo_dpo", seed)]
        v2_m = run_metrics[("clean_sft_grpo_v2", seed)]
        full_dpo_m = run_full_metrics[("clean_sft_grpo_dpo", seed)]
        full_v2_m = run_full_metrics[("clean_sft_grpo_v2", seed)]
        for metric in ("over_refusal_pct", "answer_on_unknown_pct"):
            d_clean = round(dpo_m[metric] - v2_m[metric], 2)
            d_full = round(full_dpo_m[metric] - full_v2_m[metric], 2)
            print(f"  seed {seed}  {metric}: clean-subset delta {d_clean:+.2f} pp "
                  f"({v2_m[metric]} -> {dpo_m[metric]})   |   "
                  f"full-population delta {d_full:+.2f} pp ({full_v2_m[metric]} -> {full_dpo_m[metric]})")

    # --- G5-shaped ordering deltas ------------------------------------------
    print()
    print("=" * 78)
    print("G5-shaped ordering deltas (over_refusal_pct), clean subset, NON-GATING, descriptive")
    print("=" * 78)
    for seed in SEEDS:
        grpo_dpo = run_metrics[("clean_sft_grpo_dpo", seed)]["over_refusal_pct"]
        dpo_grpo = run_metrics[("clean_sft_dpo_grpo", seed)]["over_refusal_pct"]
        grpo_kto = run_metrics[("clean_sft_grpo_kto", seed)]["over_refusal_pct"]
        kto_grpo = run_metrics[("clean_sft_kto_grpo", seed)]["over_refusal_pct"]
        full_grpo_dpo = run_full_metrics[("clean_sft_grpo_dpo", seed)]["over_refusal_pct"]
        full_dpo_grpo = run_full_metrics[("clean_sft_dpo_grpo", seed)]["over_refusal_pct"]
        full_grpo_kto = run_full_metrics[("clean_sft_grpo_kto", seed)]["over_refusal_pct"]
        full_kto_grpo = run_full_metrics[("clean_sft_kto_grpo", seed)]["over_refusal_pct"]
        print(f"  seed {seed}  DPO pair (grpo_dpo - dpo_grpo): "
              f"clean-subset {round(grpo_dpo - dpo_grpo, 2):+.2f} pp "
              f"({dpo_grpo} vs {grpo_dpo})   |   "
              f"full-population {round(full_grpo_dpo - full_dpo_grpo, 2):+.2f} pp "
              f"({full_dpo_grpo} vs {full_grpo_dpo})")
        print(f"  seed {seed}  KTO pair (grpo_kto - kto_grpo): "
              f"clean-subset {round(grpo_kto - kto_grpo, 2):+.2f} pp "
              f"({kto_grpo} vs {grpo_kto})   |   "
              f"full-population {round(full_grpo_kto - full_kto_grpo, 2):+.2f} pp "
              f"({full_kto_grpo} vs {full_grpo_kto})")

    print()
    print("=" * 78)
    print("STRUCTURAL NOTE: seed-1 scored_rows.jsonl are not on disk (NOTEBOOK.md, G3 entry); "
          "this table is seeds 2/3 only.")
    print("=" * 78)


if __name__ == "__main__":
    main()
