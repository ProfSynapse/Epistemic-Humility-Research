#!/usr/bin/env python3
"""GRPO reward v2 for schema response-confidence training.

V2 addresses the seed-1 GRPO failure mode:

1. Unknown answering dropped, but known over-refusal rose sharply.
2. Confidence stayed clustered and was higher on inappropriate refusals than
   appropriate answers.

The main change is that behavior dominates confidence. Correct known answers
and correct unknown abstentions are rewarded, but known over-refusal is strongly
negative regardless of whether the model admits low confidence. Confidence can
soften or worsen a behavior score, but it cannot turn an inappropriate response
into a good one.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import humility_reward as base_reward  # noqa: E402


@dataclass(frozen=True)
class RewardConfigV2:
    known_correct_reward: float = 2.0
    known_wrong_penalty: float = -0.8
    known_over_refusal_penalty: float = -2.0
    unknown_abstain_reward: float = 1.2
    unknown_answer_penalty: float = -1.2
    ambiguous_correct_reward: float = 0.8
    ambiguous_refusal_reward: float = 0.1
    ambiguous_wrong_penalty: float = -0.8
    invalid_json_penalty: float = 2.4
    missing_confidence_penalty: float = 0.5
    hedge_on_known_penalty: float = 0.1
    confidence_weight: float = 0.6
    confidence_tolerance: float = 0.2
    endpoint_confidence_penalty: float = 1.0
    known_correct_confidence_target: float = 0.82
    known_wrong_confidence_target: float = 0.22
    known_over_refusal_confidence_target: float = 0.18
    unknown_abstain_confidence_target: float = 0.82
    unknown_answer_confidence_target: float = 0.18
    ambiguous_answer_confidence_target: float = 0.50
    ambiguous_refusal_confidence_target: float = 0.45


def parse_completion(text: str) -> base_reward.ParsedCompletion:
    return base_reward.parse_completion(text)


def is_refusal(text: str) -> bool:
    return base_reward.is_refusal(text)


def is_correct(generation: str, aliases: Sequence[str]) -> bool:
    return base_reward.is_correct(generation, aliases)


def _label_kind(value: Any) -> str:
    return base_reward._label_kind(value)


def _coerce_completion_text(completion: Any) -> str:
    return base_reward._coerce_completion_text(completion)


def _expand(values: Any, n: int) -> list[Any]:
    return base_reward._expand(values, n)


def _has_generic_hedge(text: str) -> bool:
    return base_reward._has_generic_hedge(text)


def _confidence_adjustment(
    confidence: float,
    *,
    target: float,
    config: RewardConfigV2,
) -> float:
    """Return a bounded confidence shaping term.

    At the target this returns +confidence_weight. At one tolerance away it
    returns zero. At two or more tolerances away it returns -confidence_weight.
    Exact endpoints are separately penalized because 0/1 collapse is not useful
    for this research question.
    """
    if confidence <= 0.0 or confidence >= 1.0:
        return -config.endpoint_confidence_penalty
    distance = abs(confidence - target)
    scaled = min(distance / max(config.confidence_tolerance, 1e-9), 2.0)
    return config.confidence_weight * (1.0 - scaled)


def _behavior_and_target(
    *,
    label_kind: str,
    refused: bool,
    correct: bool,
    config: RewardConfigV2,
) -> tuple[float, float]:
    if label_kind == "ambiguous":
        if refused:
            return (
                config.ambiguous_refusal_reward,
                config.ambiguous_refusal_confidence_target,
            )
        if correct:
            return (
                config.ambiguous_correct_reward,
                config.ambiguous_answer_confidence_target,
            )
        return (
            config.ambiguous_wrong_penalty,
            config.known_wrong_confidence_target,
        )

    if label_kind == "unknown":
        if refused:
            return (
                config.unknown_abstain_reward,
                config.unknown_abstain_confidence_target,
            )
        return (
            config.unknown_answer_penalty,
            config.unknown_answer_confidence_target,
        )

    if refused:
        return (
            config.known_over_refusal_penalty,
            config.known_over_refusal_confidence_target,
        )
    if correct:
        return (
            config.known_correct_reward,
            config.known_correct_confidence_target,
        )
    return (
        config.known_wrong_penalty,
        config.known_wrong_confidence_target,
    )


def score_completion(
    completion: str,
    *,
    label: str,
    aliases: Sequence[str] | None = None,
    config: RewardConfigV2 = RewardConfigV2(),
) -> float:
    """Score one completion for a known/unknown/ambiguous labeled question."""
    parsed = parse_completion(completion)
    answer = parsed.answer_text
    label_kind = _label_kind(label)
    refused = is_refusal(answer)
    correct = False if refused else is_correct(answer, aliases or [])

    reward, confidence_target = _behavior_and_target(
        label_kind=label_kind,
        refused=refused,
        correct=correct,
        config=config,
    )

    confidence = parsed.stated_confidence
    if not parsed.valid_json:
        reward -= config.invalid_json_penalty
    elif confidence is None:
        reward -= config.missing_confidence_penalty
    else:
        reward += _confidence_adjustment(
            confidence,
            target=confidence_target,
            config=config,
        )

    if label_kind == "known" and correct and _has_generic_hedge(answer):
        reward -= config.hedge_on_known_penalty

    return float(reward)


def epistemic_humility_reward(completions, prompts=None, **kwargs) -> list[float]:
    """TRL-compatible reward function."""
    n = len(completions)
    labels = _expand(kwargs.get("label", "known"), n)
    aliases = _expand(kwargs.get("aliases", []), n)

    rewards: list[float] = []
    debug_rows: list[dict[str, Any]] = []
    for idx, completion in enumerate(completions):
        alias_value = aliases[idx]
        if isinstance(alias_value, str):
            alias_list = [alias_value]
        else:
            alias_list = list(alias_value or [])
        completion_text = _coerce_completion_text(completion)
        reward = score_completion(
            completion_text,
            label=str(labels[idx]),
            aliases=alias_list,
        )
        rewards.append(reward)
        if os.environ.get("GRPO_REWARD_DEBUG_PATH"):
            parsed = parse_completion(completion_text)
            label_kind = _label_kind(labels[idx])
            refused = is_refusal(parsed.answer_text)
            correct = False if refused else is_correct(parsed.answer_text, alias_list)
            behavior_reward, confidence_target = _behavior_and_target(
                label_kind=label_kind,
                refused=refused,
                correct=correct,
                config=RewardConfigV2(),
            )
            debug_rows.append(
                {
                    "idx": idx,
                    "label": labels[idx],
                    "label_kind": label_kind,
                    "aliases": alias_list,
                    "reward": reward,
                    "behavior_reward": behavior_reward,
                    "confidence_target": confidence_target,
                    "valid_json": parsed.valid_json,
                    "refused": refused,
                    "correct": correct,
                    "answer_text": parsed.answer_text,
                    "response_confidence": parsed.stated_confidence,
                    "completion": completion_text,
                }
            )
    _write_debug_rows(debug_rows)
    return rewards


def _write_debug_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path_value = os.environ.get("GRPO_REWARD_DEBUG_PATH")
    if not path_value:
        return
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "at": datetime.now(timezone.utc).isoformat(),
        "num_completions": len(rows),
        "rows": rows,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
