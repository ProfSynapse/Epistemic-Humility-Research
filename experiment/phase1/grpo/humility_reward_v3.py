#!/usr/bin/env python3
"""GRPO reward v3: interpretability-informed, proper-scoring confidence.

WHY v3 (the mech-interp finding that motivates it)
--------------------------------------------------
Phase-3 probing of the v2-trained model found that the emitted
``response_confidence`` had COLLAPSED to a near-constant ~0.82 (std ~0.015),
with AUROC ~0.56 at ranking its own correct vs wrong answers (ECE ~0.14), even
though an internal "doubt" axis at L35 ranks the same items cleanly
(correct > wrong > refused > unknown) and is near-calibrated by linear readout
(ECE ~0.004). The model KNOWS internally; it does not SAY.

The collapse is the v2 reward working as written. v2 shapes confidence toward a
FIXED per-cell target keyed to the realized cell (known_correct -> 0.82,
known_wrong -> 0.22, ...). But the model cannot observe its own correctness at
generation time, so it cannot condition the confidence token on "am I right".
With ~96% of answered knowns correct, emitting the majority target (~0.82) for
every answer is reward-optimal -> the number collapses to a constant. The
confidence term (weight 0.6) is also dominated by behavior (+/-2.0).

THE FIX (proper scoring rule, per-question target)
--------------------------------------------------
Replace the fixed per-cell target with a PROPER SCORING RULE (Brier) of the
stated confidence against the realized APPROPRIATENESS of the response. A proper
scoring rule is uniquely maximized, in expectation, by reporting the true
probability -- so a constant cannot win, and the optimum for a question is
``p(appropriate | question)``. Because the model's internal doubt axis already
encodes that probability, the cheapest way to satisfy the reward is to ROUTE the
internal signal to the output token. That is the mech-interp -> RL loop: we make
internal-output coherence the optimum instead of hand-specifying the number.

Per-question target, three sources (``target_mode``):
- ``"outcome"``  : per-completion realized appropriateness (0/0.5/1). Proper in
                   expectation, needs no grouping. Simplest, always available.
- ``"group"``    : the GRPO group's mean appropriateness for the prompt
                   (variance-reduced difficulty target; default). Computed from
                   the completions TRL already hands the reward -- no extra pass.
- ``"internal"`` : a precomputed per-prompt doubt-axis probe estimate passed as
                   the ``internal_confidence`` dataset column (literal
                   "align to the internal representation"). Tests faithfulness.
- ``"blend"``    : convex mix of group and internal targets.

Behavior still dominates (correct/abstain magnitudes unchanged from v2); the
confidence term can soften or sharpen but cannot turn an inappropriate response
good. This module is self-contained (stdlib + the co-located base reward) so the
Synaptic Tuner submodule can load it as a custom reward file unchanged.

GOVERNANCE: v3 is a NEW reward for a NEW (mech-interp-informed) training cell. It
does not modify the protocol-locked v2 reward or any locked run-matrix cell.
Training with v3 requires explicit user sign-off and a governed amendment.
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

VALID_TARGET_MODES = ("outcome", "group", "internal", "blend")


@dataclass(frozen=True)
class RewardConfigV3:
    # --- behavior (dominant; magnitudes carried over from v2) ---
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
    # --- confidence: proper scoring (replaces v2 fixed-target shaping) ---
    confidence_weight: float = 1.2          # raised from 0.6, still < behavior magnitudes
    endpoint_confidence_penalty: float = 0.5  # guards only exact 0/1 degeneracy
    target_mode: str = "group"
    internal_blend: float = 0.5             # weight on the internal target in "blend"
    ambiguous_refusal_appropriateness: float = 0.5


# --- reuse the v2/base parsing surface -------------------------------------

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


# --- behavior + appropriateness --------------------------------------------

def _behavior_reward(label_kind: str, refused: bool, correct: bool,
                     config: RewardConfigV3) -> float:
    """Dominant behavior term (no confidence target attached, unlike v2)."""
    if label_kind == "ambiguous":
        if refused:
            return config.ambiguous_refusal_reward
        return config.ambiguous_correct_reward if correct else config.ambiguous_wrong_penalty
    if label_kind == "unknown":
        return config.unknown_abstain_reward if refused else config.unknown_answer_penalty
    if refused:
        return config.known_over_refusal_penalty
    return config.known_correct_reward if correct else config.known_wrong_penalty


def appropriateness(label_kind: str, refused: bool, correct: bool,
                    config: RewardConfigV3) -> float:
    """Realized appropriateness in [0,1] -- the event the confidence should predict.

    Confidence is defined as P(my answer or abstention is the appropriate
    response). Appropriate = correct known answer, or abstention on an unknown.
    """
    if label_kind == "ambiguous":
        if refused:
            return config.ambiguous_refusal_appropriateness
        return 1.0 if correct else 0.0
    if label_kind == "unknown":
        return 1.0 if refused else 0.0
    # known
    if refused:
        return 0.0  # over-refusal is inappropriate
    return 1.0 if correct else 0.0


def _proper_score(confidence: float, target: float, weight: float) -> float:
    """Brier proper score, scaled to [-weight, +weight].

    +weight at confidence == target, -weight at maximal Brier (1.0). Because the
    Brier rule is proper, the expected value over a question is maximized only by
    confidence == p(appropriate | question).
    """
    brier = (confidence - target) ** 2  # in [0, 1]
    return weight * (1.0 - 2.0 * brier)


def score_completion(
    completion: str,
    *,
    label: str,
    aliases: Sequence[str] | None = None,
    p_target: float | None = None,
    config: RewardConfigV3 = RewardConfigV3(),
) -> float:
    """Score one completion. ``p_target`` is the per-question confidence target.

    If ``p_target`` is None (``outcome`` mode), the proper score uses this
    completion's own realized appropriateness as the target.
    """
    parsed = parse_completion(completion)
    answer = parsed.answer_text
    label_kind = _label_kind(label)
    refused = is_refusal(answer)
    correct = False if refused else is_correct(answer, aliases or [])

    reward = _behavior_reward(label_kind, refused, correct, config)
    app = appropriateness(label_kind, refused, correct, config)
    target = app if p_target is None else float(p_target)
    target = min(1.0, max(0.0, target))

    confidence = parsed.stated_confidence
    if not parsed.valid_json:
        reward -= config.invalid_json_penalty
    elif confidence is None:
        reward -= config.missing_confidence_penalty
    elif confidence <= 0.0 or confidence >= 1.0:
        reward -= config.endpoint_confidence_penalty  # degenerate 0/1 collapse
    else:
        reward += _proper_score(confidence, target, config.confidence_weight)

    if label_kind == "known" and correct and _has_generic_hedge(answer):
        reward -= config.hedge_on_known_penalty

    return float(reward)


# --- per-prompt target assembly (TRL entry) --------------------------------

def _completion_appropriateness(completion_text: str, label: Any,
                                aliases: Any, config: RewardConfigV3) -> float:
    parsed = parse_completion(completion_text)
    label_kind = _label_kind(label)
    refused = is_refusal(parsed.answer_text)
    alias_list = [aliases] if isinstance(aliases, str) else list(aliases or [])
    correct = False if refused else is_correct(parsed.answer_text, alias_list)
    return appropriateness(label_kind, refused, correct, config)


def _group_keys(prompts: Any, group_ids: Any, n: int) -> list[Any]:
    if group_ids is not None:
        return [str(g) for g in _expand(group_ids, n)]
    if prompts is not None:
        return [str(p) for p in _expand(prompts, n)]
    return list(range(n))  # every completion is its own group -> equals outcome mode


def _resolve_targets(
    *,
    completions_text: list[str],
    labels: list[Any],
    aliases: list[Any],
    prompts: Any,
    group_ids: Any,
    internal: list[Any] | None,
    config: RewardConfigV3,
) -> list[float | None]:
    n = len(completions_text)
    mode = config.target_mode
    if mode not in VALID_TARGET_MODES:
        raise ValueError(f"target_mode {mode!r} not in {VALID_TARGET_MODES}")

    if mode == "outcome":
        return [None] * n

    group_target: list[float] | None = None
    if mode in ("group", "blend"):
        keys = _group_keys(prompts, group_ids, n)
        apps = [
            _completion_appropriateness(completions_text[i], labels[i], aliases[i], config)
            for i in range(n)
        ]
        sums: dict[Any, float] = {}
        counts: dict[Any, int] = {}
        for k, a in zip(keys, apps):
            sums[k] = sums.get(k, 0.0) + a
            counts[k] = counts.get(k, 0) + 1
        group_target = [sums[k] / counts[k] for k in keys]

    internal_target: list[float] | None = None
    if mode in ("internal", "blend"):
        if internal is None:
            raise ValueError(
                "target_mode requires an 'internal_confidence' column but none was passed"
            )
        internal_target = [float(v) for v in internal]

    if mode == "group":
        return list(group_target)  # type: ignore[arg-type]
    if mode == "internal":
        return list(internal_target)  # type: ignore[arg-type]
    # blend
    w = config.internal_blend
    return [
        (1.0 - w) * group_target[i] + w * internal_target[i]  # type: ignore[index]
        for i in range(n)
    ]


def make_reward(config: RewardConfigV3 = RewardConfigV3()):
    """Return a TRL-compatible reward closure bound to ``config``."""

    def epistemic_humility_reward_v3(completions, prompts=None, **kwargs) -> list[float]:
        n = len(completions)
        labels = _expand(kwargs.get("label", "known"), n)
        aliases_raw = _expand(kwargs.get("aliases", []), n)
        internal_raw = kwargs.get("internal_confidence")
        internal = _expand(internal_raw, n) if internal_raw is not None else None
        group_ids = kwargs.get("group_id")

        completions_text = [_coerce_completion_text(c) for c in completions]
        targets = _resolve_targets(
            completions_text=completions_text,
            labels=labels,
            aliases=aliases_raw,
            prompts=prompts,
            group_ids=group_ids,
            internal=internal,
            config=config,
        )

        rewards: list[float] = []
        debug_rows: list[dict[str, Any]] = []
        for idx, text in enumerate(completions_text):
            alias_value = aliases_raw[idx]
            alias_list = [alias_value] if isinstance(alias_value, str) else list(alias_value or [])
            reward = score_completion(
                text,
                label=str(labels[idx]),
                aliases=alias_list,
                p_target=targets[idx],
                config=config,
            )
            rewards.append(reward)
            if os.environ.get("GRPO_REWARD_DEBUG_PATH"):
                parsed = parse_completion(text)
                debug_rows.append(
                    {
                        "idx": idx,
                        "label": labels[idx],
                        "aliases": alias_list,
                        "reward": reward,
                        "confidence_target": targets[idx],
                        "target_mode": config.target_mode,
                        "valid_json": parsed.valid_json,
                        "response_confidence": parsed.stated_confidence,
                        "answer_text": parsed.answer_text,
                        "completion": text,
                    }
                )
        _write_debug_rows(debug_rows)
        return rewards

    return epistemic_humility_reward_v3


# default closure for loaders that import a callable by name
epistemic_humility_reward = make_reward()


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
