#!/usr/bin/env python3
"""Custom GRPO reward for epistemic-humility training.

The reward separates three decisions that should not be collapsed:

1. Did the completion answer or abstain?
2. If it answered a known question, was the answer correct?
3. Did the stated confidence match the correctness/knowledge-boundary state?

This module is self-contained so Synaptic Tuner can load it as a custom reward
file without importing experiment-specific packages from the submodule.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Sequence


REFUSAL_MARKERS: tuple[str, ...] = (
    "beyond the scope of my knowledge",
    "i am not sure what the answer is",
    "i don't know the answer",
    "i do not know the answer",
)

STATED_CONFIDENCE_REFUSAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi\s+do\s+not\s+know\b", re.IGNORECASE),
    re.compile(r"\bi\s+don['\u2019]t\s+know\b", re.IGNORECASE),
    re.compile(r"^\s*abstain\b", re.IGNORECASE),
)

HEDGE_MARKERS: tuple[str, ...] = (
    "i think",
    "i believe",
    "maybe",
    "probably",
    "possibly",
    "not entirely sure",
    "not completely sure",
)

@dataclass(frozen=True)
class RewardConfig:
    correct_reward: float = 1.0
    wrong_penalty: float = -1.0
    abstain_unknown_reward: float = 0.25
    over_refusal_penalty: float = -0.6
    calibration_weight: float = 0.25
    missing_confidence_penalty: float = 0.05
    invalid_json_penalty: float = 1.0
    confident_wrong_weight: float = 0.5
    hedge_on_known_penalty: float = 0.1


@dataclass(frozen=True)
class ParsedCompletion:
    answer_text: str
    stated_confidence: float | None
    valid_json: bool


def _coerce_confidence_value(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    if parsed < 0.0 or parsed > 1.0:
        return None
    return parsed


def parse_completion(text: str) -> ParsedCompletion:
    """Split a completion into answer text and optional confidence.

    Required stated-confidence format:
    - `{"answer": "Paris", "confidence": 0.73}`
    """
    raw = str(text or "").strip()
    payload = _load_stated_confidence_payload(raw)
    if isinstance(payload, dict) and set(payload) == {"answer", "confidence"}:
        answer = payload.get("answer")
        confidence = _coerce_confidence_value(payload.get("confidence"))
        if isinstance(answer, str) and confidence is not None:
            return ParsedCompletion(
                answer_text=answer.strip(),
                stated_confidence=confidence,
                valid_json=True,
            )

    return ParsedCompletion(answer_text=raw, stated_confidence=None, valid_json=False)


def _load_stated_confidence_payload(raw: str) -> object:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    if "</think>" not in raw:
        return None
    suffix = raw.rsplit("</think>", maxsplit=1)[-1].strip()
    if not suffix:
        return None
    try:
        return json.loads(suffix)
    except json.JSONDecodeError:
        return None


def is_refusal(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(marker in lowered for marker in REFUSAL_MARKERS) or any(
        pattern.search(text) for pattern in STATED_CONFIDENCE_REFUSAL_PATTERNS
    )


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(text or "").lower()))


def is_correct(generation: str, aliases: Sequence[str]) -> bool:
    normalized_aliases = [normalize(alias) for alias in aliases if normalize(alias)]
    gen = f" {normalize(generation)} "
    return any(f" {alias} " in gen for alias in normalized_aliases)


def _has_generic_hedge(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(marker in lowered for marker in HEDGE_MARKERS)


def _as_bool_unknown(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    lowered = str(value or "").strip().lower()
    if lowered in {"unknown", "unanswerable", "false", "0"}:
        return True
    if lowered in {"known", "answerable", "true", "1"}:
        return False
    return False


def _coerce_completion_text(completion: Any) -> str:
    if isinstance(completion, str):
        return completion
    if isinstance(completion, dict):
        content = completion.get("content")
        if isinstance(content, str):
            return content
    if isinstance(completion, list) and completion:
        first = completion[0]
        if isinstance(first, dict) and isinstance(first.get("content"), str):
            return first["content"]
    return str(completion or "")


def _expand(values: Any, n: int) -> list[Any]:
    if isinstance(values, list):
        if len(values) == n:
            return values
        if len(values) == 1:
            return values * n
        if len(values) and n % len(values) == 0:
            expanded: list[Any] = []
            for value in values:
                expanded.extend([value] * (n // len(values)))
            return expanded
        if values:
            return (values + [values[-1]] * n)[:n]
    return [values] * n


def score_completion(
    completion: str,
    *,
    label: str,
    aliases: Sequence[str] | None = None,
    config: RewardConfig = RewardConfig(),
) -> float:
    """Score one completion for a known/unknown labeled question."""
    parsed = parse_completion(completion)
    answer = parsed.answer_text
    unknown = _as_bool_unknown(label)
    refused = is_refusal(answer)
    correct = False if refused else is_correct(answer, aliases or [])

    if unknown:
        reward = config.abstain_unknown_reward if refused else config.wrong_penalty
    elif refused:
        reward = config.over_refusal_penalty
    elif correct:
        reward = config.correct_reward
    else:
        reward = config.wrong_penalty

    confidence = parsed.stated_confidence
    if not parsed.valid_json:
        reward -= config.invalid_json_penalty
    elif confidence is None:
        reward -= config.missing_confidence_penalty
    else:
        confidence_target = 1.0 if (not unknown and correct) else 0.0
        calibration_reward = 1.0 - 2.0 * ((confidence - confidence_target) ** 2)
        reward += config.calibration_weight * calibration_reward

        if (unknown and not refused) or ((not unknown) and not refused and not correct):
            reward -= config.confident_wrong_weight * confidence

    if (not unknown) and correct and _has_generic_hedge(answer):
        reward -= config.hedge_on_known_penalty

    return float(reward)


def epistemic_humility_reward(completions, prompts=None, **kwargs) -> list[float]:
    """TRL-compatible reward function.

    Expected dataset columns passed through `kwargs`:
    - `label`: "known" or "unknown"
    - `aliases`: list of acceptable answer aliases for known rows
    """
    n = len(completions)
    labels = _expand(kwargs.get("label", "known"), n)
    aliases = _expand(kwargs.get("aliases", []), n)

    rewards: list[float] = []
    for idx, completion in enumerate(completions):
        alias_value = aliases[idx]
        if isinstance(alias_value, str):
            alias_list = [alias_value]
        else:
            alias_list = list(alias_value or [])
        rewards.append(
            score_completion(
                _coerce_completion_text(completion),
                label=str(labels[idx]),
                aliases=alias_list,
            )
        )
    return rewards
