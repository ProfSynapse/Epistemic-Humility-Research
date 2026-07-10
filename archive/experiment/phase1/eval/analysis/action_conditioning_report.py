#!/usr/bin/env python3
"""Action-conditioning report: does the answer/abstain ACTION track knowledge?

Motivation (Amendment N, session 0026 cp 020/021)
--------------------------------------------------
GRPO-on-K produced calibrated *confidence* (the emitted ``response_confidence``
scalar discriminates known/unknown, AUROC ~0.65, cells ordered) while the
answer/abstain *action* appeared knowledge-INDEPENDENT: greedy decode refuses
~everything (over_refusal 91%), temp 1.35 answers ~everything (refusal 8%), and
at neither operating point does the action discriminate known from unknown.

This script quantifies that decoupling from a single ``scored_rows.jsonl`` and,
optionally, traces the action margin across training from a GRPO reward-debug
JSONL. It is the deterministic computation of the Amendment N re-run FALSIFIER:

    Re-run falsifier: if the answer-rate margin between knowns and unknowns does
    NOT open up (P(answer|known) - P(answer|unknown) stays ~0), the action stays
    a global propensity knob -> the action-conditioning failure is STRUCTURAL,
    not a KL artifact -> stop tuning beta and write it up.

Two complementary measurements:
  1. ACTION channel: P(answer | known) vs P(answer | unknown). The margin (with a
     two-proportion z-test) is how much the *decision* tracks knowledge.
  2. CONFIDENCE channel: among refusals, AUROC of stated_confidence separating
     unknown-refused (appropriate) from known-refused (a mistake). High AUROC =
     the confidence scalar "knows" the refusal was wrong even though the action
     didn't. The gap between (2) high and (1) ~0 IS "calibrated confidence,
     uncalibrated action".

stdlib only (manual AUROC + normal-approx z-test); no sklearn/scipy/numpy.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


# --------------------------------------------------------------------------- io

def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ------------------------------------------------------------------ statistics

def _auroc(scores_pos: list[float], scores_neg: list[float]) -> float | None:
    """AUROC via the Mann-Whitney U / rank-sum identity. None if either empty."""
    if not scores_pos or not scores_neg:
        return None
    combined = [(s, 1) for s in scores_pos] + [(s, 0) for s in scores_neg]
    combined.sort(key=lambda t: t[0])
    # average ranks for ties
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-based average rank
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    sum_pos = sum(r for r, (_, lab) in zip(ranks, combined) if lab == 1)
    n_pos, n_neg = len(scores_pos), len(scores_neg)
    u = sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def _two_proportion_z(k1: int, n1: int, k2: int, n2: int) -> dict[str, float | None]:
    """Two-proportion z-test (pooled). Returns p1, p2, diff, z, two-sided p."""
    if n1 == 0 or n2 == 0:
        return {"p1": None, "p2": None, "diff": None, "z": None, "p_value": None}
    p1, p2 = k1 / n1, k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return {"p1": p1, "p2": p2, "diff": p1 - p2, "z": None, "p_value": None}
    z = (p1 - p2) / se
    p_value = math.erfc(abs(z) / math.sqrt(2.0))  # two-sided normal approx
    return {"p1": p1, "p2": p2, "diff": p1 - p2, "z": z, "p_value": p_value}


# ----------------------------------------------------------------- core report

def _is_refused(row: dict[str, Any]) -> bool:
    return bool(row.get("refused"))


def action_conditioning(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_label[str(r.get("label", "known"))].append(r)

    known, unknown = by_label.get("known", []), by_label.get("unknown", [])

    def answered(rs: list[dict[str, Any]]) -> int:
        return sum(1 for r in rs if not _is_refused(r))

    k_ans, u_ans = answered(known), answered(unknown)
    # ACTION margin: P(answer|known) - P(answer|unknown). Positive = the decision
    # tracks knowledge (answers what it knows more than what it doesn't).
    action = _two_proportion_z(k_ans, len(known), u_ans, len(unknown))

    # CONFIDENCE channel among refusals: can the scalar tell a mistaken refusal
    # (known-refused) from a correct one (unknown-refused)?
    known_refused_conf = [r["stated_confidence"] for r in known
                          if _is_refused(r) and r.get("stated_confidence") is not None]
    unknown_refused_conf = [r["stated_confidence"] for r in unknown
                            if _is_refused(r) and r.get("stated_confidence") is not None]
    refusal_conf_auroc = _auroc(unknown_refused_conf, known_refused_conf)

    # CONFIDENCE channel among answers: separate correct from wrong answers.
    ans_correct = [r["stated_confidence"] for r in rows
                   if not _is_refused(r) and r.get("correct") and r.get("stated_confidence") is not None]
    ans_wrong = [r["stated_confidence"] for r in rows
                 if not _is_refused(r) and not r.get("correct") and r.get("stated_confidence") is not None]
    answer_conf_auroc = _auroc(ans_correct, ans_wrong)

    def _mean(xs: list[float]) -> float | None:
        return sum(xs) / len(xs) if xs else None

    return {
        "n": len(rows),
        "n_known": len(known),
        "n_unknown": len(unknown),
        "action_channel": {
            "answer_rate_known": action["p1"],
            "answer_rate_unknown": action["p2"],
            "margin_known_minus_unknown": action["diff"],
            "z": action["z"],
            "p_value": action["p_value"],
            "answered_known": k_ans,
            "answered_unknown": u_ans,
        },
        "confidence_channel": {
            "refusal_appropriateness_auroc": refusal_conf_auroc,
            "known_refused_conf_mean": _mean(known_refused_conf),
            "unknown_refused_conf_mean": _mean(unknown_refused_conf),
            "n_known_refused": len(known_refused_conf),
            "n_unknown_refused": len(unknown_refused_conf),
            "answer_correctness_auroc": answer_conf_auroc,
            "answer_correct_conf_mean": _mean(ans_correct),
            "answer_wrong_conf_mean": _mean(ans_wrong),
        },
    }


# ----------------------------------------------- training-trajectory (optional)

def _reward_debug_action_trajectory(path: Path, n_bins: int = 5) -> dict[str, Any]:
    """From a GRPO reward-debug JSONL, bin events into n_bins over training and
    compute the answer-rate margin (known vs unknown) per bin -- did the action
    ever start tracking knowledge during training?"""
    events = _load_jsonl(path)
    n = len(events)
    if n == 0:
        return {"events": 0}

    def refused(text_row: dict[str, Any]) -> bool:
        ans = (text_row.get("answer_text") or "").lower()
        return ("don't know" in ans or "dont know" in ans or "do not know" in ans
                or ("cannot" in ans and "answer" in ans))

    bins = []
    edges = [int(n * i / n_bins) for i in range(n_bins + 1)]
    for b in range(n_bins):
        chunk = events[edges[b]:edges[b + 1]]
        k_ans = k_tot = u_ans = u_tot = 0
        for e in chunk:
            for r in e.get("rows", []):
                lab = r.get("label", "known")
                ans = not refused(r)
                if lab == "known":
                    k_tot += 1
                    k_ans += ans
                elif lab == "unknown":
                    u_tot += 1
                    u_ans += ans
        pk = k_ans / k_tot if k_tot else None
        pu = u_ans / u_tot if u_tot else None
        bins.append({
            "bin": b,
            "step_range": [edges[b], edges[b + 1]],
            "answer_rate_known": pk,
            "answer_rate_unknown": pu,
            "margin": (pk - pu) if (pk is not None and pu is not None) else None,
        })
    return {"events": n, "n_bins": n_bins, "bins": bins}


# ------------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scored", type=Path, help="scored_rows.jsonl from run_eval")
    ap.add_argument("--reward-debug", type=Path,
                    help="GRPO reward-debug JSONL (training-trajectory action margin)")
    ap.add_argument("--bins", type=int, default=5, help="trajectory bins (default 5)")
    ap.add_argument("--out", type=Path, help="write JSON report here too")
    args = ap.parse_args(argv)

    report: dict[str, Any] = {}
    if args.scored:
        report["scored_rows"] = str(args.scored)
        report["eval"] = action_conditioning(_load_jsonl(args.scored))
    if args.reward_debug:
        report["reward_debug"] = str(args.reward_debug)
        report["training_trajectory"] = _reward_debug_action_trajectory(
            args.reward_debug, n_bins=args.bins)
    if not report:
        ap.error("provide --scored and/or --reward-debug")

    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
