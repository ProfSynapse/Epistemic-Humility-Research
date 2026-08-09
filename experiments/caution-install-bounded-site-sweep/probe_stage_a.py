#!/usr/bin/env python3
"""caution-install-bounded-site-sweep pre-sign feasibility probe, Stage A.

CPU only. No model, no generation. Per feasibility_probe.yaml
`stage_a_corpus_inventory`:

  - counts the candidate rows available to draw from (M_u gold-unanswerable,
    M_a gold-answerable), so Stage B's measured role rates can be converted
    into an achievable pool size (pass criterion P1/P2);
  - verifies the candidate rows are disjoint from the training pool consumed
    by the clean-SFT / GRPO-v2 stages of this lineage (pass criterion P4);
  - draws the 400 + 400 row sample Stage B will generate on, deterministically
    at seed 20260707, and records it to a gitignored private manifest so
    Stage B (and later the main cell's Stage 1 mining) can reuse it verbatim.

Candidate source: experiments/divergent-pool-own-readout's phase1-migrated
mirror of the AH stage-0 expansion candidates
(expansion_candidates.jsonl, 13,496 rows: 3,496 kuq_ku_unknown_x [label
"unknown"], 6,000 triviaqa + 4,000 popqa [label "known", carrying gold
aliases]), the same corpus and the same candidate_rows() filter semantics as
experiments/j-space-cross-family-layer-contrast/mine_eval_pool.py.

Training-pool source for the disjointness check: the clean-SFT / GRPO-v2
lineage's WS-0 probe pool is pinned to
`datasets/triviaqa-rc-nocontext/train.jsonl` by
experiments/common/configs/knowledge-probe/probe.yaml (`probe_pool.train_jsonl`,
"Every field here is pinned and pre-registered in
archive/docs/protocols/phase1/PROTOCOL.md v0.3"), subset-capped at 20,000
questions. This script checks against the FULL train.jsonl (a conservative
superset of the actual ~20k training subset), so a pass here is a pass
against any subset of it. The candidate corpus's own "triviaqa" source draws
from `datasets/triviaqa-rc-nocontext/validation.jsonl` (a different split,
per archive/experiment/phase1/probe/amendments/amendment_ah_stage0_expand_candidates.py),
and the "popqa" / "kuq_ku_unknown_x" sources are different datasets entirely
that never feed this lineage's training pool; the join below still checks
every candidate row by normalized question text against the full train set,
rather than assuming disjointness by source label.

Output: analysis-committed/probe_corpus_inventory.json (public: counts,
rates, disjointness result -- no question text, no aliases) and
analysis/probe_sampled_rows_private.jsonl (gitignored: the 800 sampled rows
with question text and aliases, for Stage B and later Stage-1 mining reuse).
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from probe_common import norm_question, wilson_lower_95  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
EXPANSION_CANDIDATES = (
    CANONICAL
    / "experiments/divergent-pool-own-readout/analysis/phase1-migrated"
    / "probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl"
)
TRAIN_JSONL = CANONICAL / "datasets/triviaqa-rc-nocontext/train.jsonl"

SEED = 20260707
N_UNANSWERABLE = 400
N_ANSWERABLE = 400
REQUIRED_HELD_OUT_CONFAB = 150
REQUIRED_HELD_OUT_KNOWN_CORRECT = 250
REQUIRED_TOTAL_CONFAB = 250
REQUIRED_TOTAL_KNOWN_CORRECT = 417

OUT_PRIVATE = HERE / "analysis" / "probe_sampled_rows_private.jsonl"
OUT_PUBLIC = HERE / "analysis-committed" / "probe_corpus_inventory.json"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_candidates() -> tuple[list[dict], list[dict]]:
    """Return (unknown_rows, known_rows) using mine_eval_pool.py's
    candidate_rows() filter semantics: unknown label as-is; known label only
    when aliases are present."""
    unknown, known = [], []
    for row in load_jsonl(EXPANSION_CANDIDATES):
        label = row.get("label")
        if label == "unknown":
            unknown.append(row)
        elif label == "known" and row.get("aliases"):
            known.append(row)
    return unknown, known


def training_pool_norm_questions(path: Path) -> tuple[set[str], int]:
    """Normalized-question set of the FULL training-pool source file (a
    conservative superset of the actual subset-capped training pool)."""
    seen: set[str] = set()
    n_rows = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n_rows += 1
            row = json.loads(line)
            q = row.get("question")
            if q:
                seen.add(norm_question(q))
    return seen, n_rows


def sample_rows(rows: list[dict], n: int, seed: int) -> list[dict]:
    ordered = sorted(rows, key=lambda r: r["row_key"])
    rng = random.Random(seed)
    return rng.sample(ordered, n)


def main() -> int:
    t0 = time.time()

    print("[stage-a] loading candidate corpus", flush=True)
    unknown_rows, known_rows = load_candidates()
    m_u = len(unknown_rows)
    m_a = len(known_rows)
    print(f"[stage-a] M_u (gold-unanswerable candidates) = {m_u}", flush=True)
    print(f"[stage-a] M_a (gold-answerable candidates)   = {m_a}", flush=True)

    print("[stage-a] loading training-pool question set for disjointness check "
          f"({TRAIN_JSONL})", flush=True)
    train_norm_questions, n_train_rows = training_pool_norm_questions(TRAIN_JSONL)
    print(f"[stage-a] training pool rows scanned = {n_train_rows}, "
          f"distinct normalized questions = {len(train_norm_questions)}", flush=True)

    overlap_rows = []
    for row in unknown_rows + known_rows:
        nq = norm_question(row.get("question", ""))
        if nq in train_norm_questions:
            overlap_rows.append(row["row_key"])
    overlap_count = len(overlap_rows)
    p4_pass = overlap_count == 0
    print(f"[stage-a] P4 disjointness overlap count = {overlap_count} "
          f"({'PASS' if p4_pass else 'FAIL'})", flush=True)

    # Arithmetic-unpassable precheck (max conceivable Wilson lower bound at
    # n=400 is achieved at successes=400/400; if even that can't clear the
    # floor, no Stage B measurement can pass P1/P2).
    max_p1_bound = wilson_lower_95(N_UNANSWERABLE, N_UNANSWERABLE) * m_u
    max_p2_bound = wilson_lower_95(N_ANSWERABLE, N_ANSWERABLE) * m_a
    p1_arithmetically_possible = max_p1_bound >= REQUIRED_TOTAL_CONFAB
    p2_arithmetically_possible = max_p2_bound >= REQUIRED_TOTAL_KNOWN_CORRECT
    print(f"[stage-a] P1 best-case bound (confab_rate=400/400) = "
          f"{max_p1_bound:.2f} vs required {REQUIRED_TOTAL_CONFAB} "
          f"({'possible' if p1_arithmetically_possible else 'ARITHMETICALLY UNPASSABLE'})",
          flush=True)
    print(f"[stage-a] P2 best-case bound (known_correct_rate=400/400) = "
          f"{max_p2_bound:.2f} vs required {REQUIRED_TOTAL_KNOWN_CORRECT} "
          f"({'possible' if p2_arithmetically_possible else 'ARITHMETICALLY UNPASSABLE'})",
          flush=True)

    stop_before_stage_b = not (p1_arithmetically_possible and p2_arithmetically_possible)

    print(f"[stage-a] sampling {N_UNANSWERABLE} unknown + {N_ANSWERABLE} known rows "
          f"uniformly without replacement at seed {SEED}", flush=True)
    sampled_unknown = sample_rows(unknown_rows, N_UNANSWERABLE, SEED)
    sampled_known = sample_rows(known_rows, N_ANSWERABLE, SEED)

    OUT_PRIVATE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PRIVATE.open("w", encoding="utf-8") as fh:
        for row in sampled_unknown:
            fh.write(json.dumps({
                "row_key": row["row_key"], "label": "unknown",
                "question": row["question"], "aliases": [],
                "source": row.get("source"), "category": row.get("category", ""),
            }, ensure_ascii=False) + "\n")
        for row in sampled_known:
            fh.write(json.dumps({
                "row_key": row["row_key"], "label": "known",
                "question": row["question"], "aliases": row.get("aliases", []),
                "source": row.get("source"), "category": row.get("category", ""),
            }, ensure_ascii=False) + "\n")
    print(f"[stage-a] wrote {len(sampled_unknown) + len(sampled_known)} sampled rows "
          f"(private, gitignored) -> {OUT_PRIVATE}", flush=True)

    public = {
        "stage": "caution_install_bounded_site_sweep_feasibility_probe_stage_a",
        "seed": SEED,
        "candidate_source": str(EXPANSION_CANDIDATES),
        "training_pool_source": str(TRAIN_JSONL),
        "training_pool_source_note": (
            "full train.jsonl scanned as a conservative superset of the "
            "actual subset-capped (max_questions=20000) WS-0 training pool "
            "pinned by experiments/common/configs/knowledge-probe/probe.yaml"
        ),
        "counts": {
            "M_u_gold_unanswerable_candidates": m_u,
            "M_a_gold_answerable_candidates": m_a,
            "training_pool_rows_scanned": n_train_rows,
            "training_pool_distinct_norm_questions": len(train_norm_questions),
        },
        "p4_disjointness": {
            "overlap_count": overlap_count,
            "pass_if": "== 0",
            "pass": p4_pass,
        },
        "arithmetic_precheck": {
            "p1_best_case_bound": round(max_p1_bound, 4),
            "p1_required_total_confab": REQUIRED_TOTAL_CONFAB,
            "p1_arithmetically_possible": p1_arithmetically_possible,
            "p2_best_case_bound": round(max_p2_bound, 4),
            "p2_required_total_known_correct": REQUIRED_TOTAL_KNOWN_CORRECT,
            "p2_arithmetically_possible": p2_arithmetically_possible,
            "stop_before_stage_b": stop_before_stage_b,
        },
        "sample": {
            "n_unanswerable_drawn": len(sampled_unknown),
            "n_answerable_drawn": len(sampled_known),
            "draw_seed": SEED,
            "draw": "uniform without replacement, sorted by row_key then rng.sample",
        },
        "runtime_sec": round(time.time() - t0, 1),
    }
    OUT_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    OUT_PUBLIC.write_text(json.dumps(public, indent=2), encoding="utf-8")
    print(f"[stage-a] wrote public inventory -> {OUT_PUBLIC}", flush=True)
    print(json.dumps(public, indent=2), flush=True)

    if stop_before_stage_b:
        print("[stage-a] STOP: Stage A counts make P1 and/or P2 arithmetically "
              "unpassable. Do not run Stage B.", file=sys.stderr, flush=True)
        return 1
    if not p4_pass:
        print("[stage-a] NOTE: P4 disjointness FAILED (overlap_count > 0). "
              "Stage B may still run per the lead's instruction to run Stage A "
              "then proceed unless P1/P2 are arithmetically unpassable, but the "
              "probe cannot pass overall.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
