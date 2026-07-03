#!/usr/bin/env python3
"""Amendment AH Stage-0 (script 6) — gold-audit sample (CPU).

Pre-registered in
experiment/protocol/AMENDMENT-AH-divergent-pool-own-readout.md (§4 step 6).

Dumps 20 random D-over and 20 random D-under rows for the orchestrator's manual
gold-label audit. Each row: question, gold label, probe scores (L20/L24/L28 +
fold), and (for D-under) the model's forced-best-guess answer + correctness.

D-over pool  = probe-certain (L24>0) AND gold-unanswerable (loosest rule).
D-under pool = the behaviorally-verified D-under set (verify/dunder_verified.jsonl),
               so the audit sees the model's actual answer.

Deterministic sample (seed 20260703).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
DEFAULT_ROOT = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
SEED = 20260703
N_PER_CELL = 20


def load_jsonl(path: Path):
    rows = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def run(args) -> int:
    root = Path(args.root).resolve()
    rng = random.Random(SEED)

    scored = load_jsonl(root / "score" / "scored_rows.jsonl")
    # D-over pool: L24>0 & gold unanswerable.
    d_over_pool = [r for r in scored
                   if r["score_L24"] > 0 and r["label"] == "unknown"]

    # D-under pool: verified set (has answer_text + correct).
    verified = load_jsonl(root / "verify" / "dunder_verified.jsonl")

    def sample(pool, n):
        pool = list(pool)
        rng.shuffle(pool)
        return pool[:n]

    d_over_sample = sample(d_over_pool, N_PER_CELL)
    d_under_sample = sample(verified, N_PER_CELL)

    def over_rec(r):
        return {
            "cell": "D_over", "row_key": r["row_key"], "question": r["question"],
            "gold_label": "unanswerable", "source": r["source"],
            "score_L20": round(r["score_L20"], 3),
            "score_L24": round(r["score_L24"], 3),
            "score_L28": round(r["score_L28"], 3),
            "fold_scores": [round(x, 3) for x in r["fold_scores"]],
            "model_forced_answer": None, "forced_answer_correct": None,
        }

    def under_rec(r):
        return {
            "cell": "D_under", "row_key": r["row_key"], "question": r["question"],
            "gold_label": "answerable", "gold_aliases": r["aliases"],
            "source": r["source"],
            "score_L20": round(r["score_L20"], 3),
            "score_L24": round(r["score_L24"], 3),
            "score_L28": round(r["score_L28"], 3),
            "fold_scores": [round(x, 3) for x in r["fold_scores"]],
            "model_forced_answer": r["answer_text"],
            "forced_answer_correct": r["correct"],
        }

    audit = {
        "amendment": "AH", "stage": "stage0_audit_sample", "seed": SEED,
        "n_per_cell": N_PER_CELL,
        "d_over_pool_size": len(d_over_pool),
        "d_under_pool_size": len(verified),
        "d_over": [over_rec(r) for r in d_over_sample],
        "d_under": [under_rec(r) for r in d_under_sample],
    }
    out = root / "audit_sample.json"
    out.write_text(json.dumps(audit, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"[ah/audit] D-over sample={len(audit['d_over'])} "
          f"D-under sample={len(audit['d_under'])} -> {out}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
