#!/usr/bin/env python3
"""CPU preflight for the v3 proper-scoring GRPO reward (B0 de-risk, GPU-free).

Re-scores REAL GRPO rollouts (a `reward_debug` JSONL) with the v3 reward and
answers the three gating questions from
`archive/notes/experiments/computed-confidence-alignment-regimen.md`:

  Q1 (THE RISK): do the v3 `group` targets actually SPREAD across prompts? If every
      prompt's mean-appropriateness is ~the same, the Brier optimum is ~constant and
      v3 collapses one level up (the SFT target-imbalance problem, redux).
  Q2: does v3 preserve the behavior ordering on real completions
      (known_correct > unknown_abstain > known_wrong > known_over_refusal)?
  Q3: on real data, does emitting the group target beat a flat constant (Brier)?

`reward_debug` records are `{at, num_completions, rows:[...]}`; each row is one
completion. Older logs omit derived `refused`/`correct`, so they are re-derived
with the BASE reward's own `is_refusal`/`is_correct` (the same matchers v3 uses
in-loop, so preflight and training agree by construction). Prompts are grouped by
(label, gold-answer set) as a stand-in for prompt identity.

Usage:
  python experiment/phase1/grpo/v3_reward_preflight.py <reward_debug.jsonl> [--flat 0.82]
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

GRPO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GRPO_DIR))

import humility_reward as base  # noqa: E402
import humility_reward_v3 as v3  # noqa: E402


def label_kind(label: str) -> str:
    label = (label or "").lower()
    if label.startswith("known"):
        return "known"
    if label.startswith("unknown"):
        return "unknown"
    return "ambiguous"


def behavior_cell(label: str, refused: bool, correct: bool) -> str:
    kind = label_kind(label)
    if kind == "known":
        if refused:
            return "known_over_refusal"
        return "known_correct" if correct else "known_wrong"
    if kind == "unknown":
        return "unknown_abstain" if refused else "unknown_answer"
    return "ambiguous"


def load_completions(path: Path) -> list[dict]:
    comps: list[dict] = []
    for line in path.open(encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        for row in rec.get("rows", []):
            ans = row.get("answer_text", "")
            aliases = tuple(sorted(a.lower() for a in (row.get("aliases") or [])))
            refused = base.is_refusal(ans)
            correct = bool(base.is_correct(ans, list(aliases))) and not refused
            comps.append({
                "label": (row.get("label") or "").lower(),
                "aliases": aliases,
                "refused": refused,
                "correct": correct,
                "completion": row.get("completion", ""),
            })
    return comps


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reward_debug", type=Path, help="path to a reward_debug JSONL")
    ap.add_argument("--flat", type=float, default=0.82,
                    help="the collapsed constant confidence to compare against (default 0.82)")
    args = ap.parse_args()

    cfg = v3.RewardConfigV3()
    comps = load_completions(args.reward_debug)
    if not comps:
        print("no completions found", file=sys.stderr)
        return 1
    print(f"completions={len(comps)}  source={args.reward_debug}")

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for c in comps:
        groups[(c["label"], c["aliases"])].append(c)

    group_target = {}
    for key, members in groups.items():
        kind = label_kind(key[0])
        appr = [v3.appropriateness(kind, m["refused"], m["correct"], cfg) for m in members]
        group_target[key] = sum(appr) / len(appr)

    tvals = list(group_target.values())
    spread = st.pstdev(tvals)
    frac_mid = sum(1 for t in tvals if 0.2 <= t <= 0.8) / len(tvals)
    print(f"\n=== Q1: group-target spread across {len(tvals)} distinct prompts ===")
    print(f"  mean={st.mean(tvals):.3f}  std={spread:.3f}  min={min(tvals):.3f}  max={max(tvals):.3f}")
    print(f"  fraction in [0.2,0.8] (genuinely graded): {frac_mid:.1%}")
    print(f"  VERDICT: {'SPREAD OK — v3 has per-prompt signal' if spread > 0.15 else 'NEAR-CONSTANT — collapse risk one level up'}")

    cell_rewards: dict[str, list[float]] = defaultdict(list)
    for c in comps:
        tgt = group_target[(c["label"], c["aliases"])]
        s = v3.score_completion(c["completion"], label=c["label"],
                                aliases=list(c["aliases"]), p_target=tgt, config=cfg)
        cell_rewards[behavior_cell(c["label"], c["refused"], c["correct"])].append(s)

    print("\n=== Q2: mean v3 reward by behavior cell (real rollouts) ===")
    means = {}
    for cl in ["known_correct", "unknown_abstain", "ambiguous",
               "known_wrong", "known_over_refusal", "unknown_answer"]:
        if cell_rewards[cl]:
            means[cl] = st.mean(cell_rewards[cl])
            print(f"  {cl:20s} n={len(cell_rewards[cl]):6d}  mean_reward={means[cl]:+.3f}")
    ok = (means.get("known_correct", 1e9) > means.get("unknown_abstain", -1e9)
          > means.get("known_wrong", -1e9) > means.get("known_over_refusal", -1e9))
    print(f"  ORDERING known_correct > unknown_abstain > known_wrong > known_over_refusal: {ok}")

    gains = [v3._proper_score(group_target[k], group_target[k], cfg.confidence_weight)
             - v3._proper_score(args.flat, group_target[k], cfg.confidence_weight)
             for k in groups]
    wins = sum(1 for g in gains if g > 1e-9)
    print(f"\n=== Q3: per-prompt Brier gain, calibrated target vs flat {args.flat} ===")
    print(f"  mean(cal - flat) = {st.mean(gains):+.3f}   calibrated strictly wins on {wins}/{len(gains)} prompts")

    green = spread > 0.15 and ok and wins == len(gains)
    print(f"\nPREFLIGHT: {'GREEN — B0 well-posed' if green else 'NOT GREEN — inspect above'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
