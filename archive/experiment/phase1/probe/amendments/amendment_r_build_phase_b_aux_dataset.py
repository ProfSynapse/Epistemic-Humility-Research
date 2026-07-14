#!/usr/bin/env python3
"""Amendment R — build the Phase B aux_head datasets (deterministic, lab-notebook).

Phase B co-trains the aux_head on the SAME clean-SFT abstention data the headline SFT
arm used (known->answer rows, unknown->abstention rows; arch doc §4.4). The aux_head
``target_field`` is the per-row ANSWERABILITY label: 1.0 if the row answers (known),
0.0 if it abstains (unknown). The builder derives that label from the assistant
completion using the CANONICAL refusal patterns (every abstention phrasing in
``abstention_bank.json`` is guaranteed to contain a refusal marker), so the derivation
is reliable, not heuristic — the builder asserts this invariant at startup.

Emits two datasets (rows = {"conversations": [...], "aux_target": 0.0|1.0}):
  - phase_b_aux_train.jsonl           real targets        (A1 treatment; A0 ignores it)
  - phase_b_aux_train_shuffled.jsonl  seed-permuted target (A2 placebo) — same marginal,
                                      broken question<->target correspondence.

Outputs go to a gitignored scratch dir (the source SFT data is restricted / not
tracked, so derived copies must not be committed either). The run recipes stage from
here exactly as the headline SFT recipe stages sft_train.jsonl.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from path_compat import repo_root  # noqa: E402

REPO = repo_root()

# Canonical refusal patterns — copied verbatim from
# experiment/phase1/grpo/build_schema_response_confidence_datasets.py:81-89
# (single source of truth for refusal detection across the project). Kept in sync by
# the abstention_bank invariant check below.
REFUSAL_PATTERNS = (
    re.compile(r"\bi\s+(?:do\s+not|don't)\s+know\b", re.I),
    re.compile(r"\bi\s+am\s+not\s+sure\b", re.I),
    re.compile(r"\bi'm\s+not\s+sure\b", re.I),
    re.compile(r"\bnot\s+sure\s+what\s+the\s+answer\s+is\b", re.I),
    re.compile(r"\bcan't\s+say\s+for\s+certain\b", re.I),
    re.compile(r"\bcannot\s+say\s+for\s+certain\b", re.I),
    re.compile(r"\bbeyond\s+the\s+scope\s+of\s+my\s+knowledge\b", re.I),
    re.compile(r"\brefrain\s+from\s+guessing\b", re.I),
)


def is_refusal(text: str) -> bool:
    return any(p.search(text or "") for p in REFUSAL_PATTERNS)


def assistant_content(conv: list[dict]) -> str:
    for turn in reversed(conv):
        if turn.get("role") == "assistant":
            return turn.get("content", "")
    raise ValueError("row has no assistant turn")


def assert_abstention_bank_invariant() -> None:
    """Every phrasing in the abstention bank MUST be detected as a refusal."""
    bank = json.loads((REPO / "experiment/phase1/data/abstention_bank.json").read_text())
    misses = [p for p in bank.get("phrasings", []) if not is_refusal(p)]
    if misses:
        raise SystemExit(f"REFUSAL_PATTERNS out of sync with abstention_bank.json; missed: {misses}")
    print(f"[build] abstention_bank invariant OK ({len(bank.get('phrasings', []))} phrasings all detected)")


def stable_permutation(n: int, seed: int) -> list[int]:
    """Deterministic permutation without Math.random/Date (Fisher-Yates, LCG)."""
    idx = list(range(n))
    state = (seed * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
    for i in range(n - 1, 0, -1):
        state = (state * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        j = state % (i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    return idx


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="experiment/phase1/data/qwen3-4b-instruct/sft_train.jsonl")
    ap.add_argument("--out-dir", default="scratch/amendment_r/phase_b")
    ap.add_argument("--shuffle-seed", type=int, default=20260629)
    a = ap.parse_args()

    assert_abstention_bank_invariant()

    src = REPO / a.src
    rows = [json.loads(l) for l in src.open(encoding="utf-8") if l.strip()]
    targets = [0.0 if is_refusal(assistant_content(r["conversations"])) else 1.0 for r in rows]
    n = len(rows)
    n_known = int(sum(targets))
    print(f"[build] n={n}  known(answer)={n_known}  unknown(abstain)={n - n_known}  "
          f"answerable_frac={n_known / n:.4f}")

    out_dir = REPO / a.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    real_path = out_dir / "phase_b_aux_train.jsonl"
    with real_path.open("w", encoding="utf-8") as f:
        for r, t in zip(rows, targets):
            f.write(json.dumps({"conversations": r["conversations"], "aux_target": t}) + "\n")

    perm = stable_permutation(n, a.shuffle_seed)
    shuffled = [targets[i] for i in perm]
    # placebo integrity: same marginal, correspondence broken
    same = sum(1 for o, s in zip(targets, shuffled) if o == s)
    print(f"[build] shuffle: marginal preserved (known still {int(sum(shuffled))}); "
          f"target unchanged on {same}/{n} rows ({same / n:.3f}) — rest decorrelated")

    shuf_path = out_dir / "phase_b_aux_train_shuffled.jsonl"
    with shuf_path.open("w", encoding="utf-8") as f:
        for r, t in zip(rows, shuffled):
            f.write(json.dumps({"conversations": r["conversations"], "aux_target": t}) + "\n")

    print(f"[build] wrote:\n  {real_path}\n  {shuf_path}")
    print("[build] A0 (LM-only) trains on the real file with aux_head disabled; "
          "A1 (joint) on the real file; A2 (placebo) on the shuffled file.")


if __name__ == "__main__":
    main()
