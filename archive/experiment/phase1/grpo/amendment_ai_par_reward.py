#!/usr/bin/env python3
"""Amendment AI — Probe-as-Reward (PAR) GRPO reward (prereg §1.2).

TRL calls this per generation batch as reward_func(prompts, completions, **kwargs)
where kwargs carries the dataset columns (row_key, question, label, gold_answerable,
aliases, ...) and trainer_state. Per rollout, with p = P(unanswerable) read at the
PRE-GENERATION anchor from the policy's OWN state:

    R_agree = p if abstained else (1 - p)
    + w_c (answered ∧ gold-answerable ∧ correct)      w_c = 0.50
    + w_a (abstained ∧ gold-unanswerable)             w_a = 0.50
    format hard gate -1.0 (schema-invalid) OVERRIDES everything.

p is read ONCE per unique row_key in the batch (identical for all G rollouts of a
prompt) from the LIVE policy model via the probe-render surface the v2 sensor was
fit on — render_probe_prompt(baseline_system, question), hidden_states[24] at
prompt_len-1, sigmoid(-score) — exactly the read the smoke validated (C2 exact 0).

Wiring: the launcher sets the module globals MODEL / TOKENIZER / PROBE /
BASELINE_SYSTEM / LOG_PATH before trainer.train(), and (permuted arm only)
PERMUTATION (row_key -> row_key within gold class). Nothing here loads the model;
it reads the same object the trainer is optimizing, so p tracks the live policy.

This module is byte-consistent with amendment_ai_smoke.py's ai_reward + pregen_p
(the smoke is the plumbing proof of exactly this path).
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np

THIS_DIR = Path(__file__).resolve().parent
PROBE_DIR = THIS_DIR.parent / "probe"
for _p in (str(THIS_DIR), str(PROBE_DIR)):
    if _p not in os.sys.path:
        os.sys.path.insert(0, _p)

import humility_reward as base_reward  # noqa: E402

# ---- constants (prereg §1.2; derived, not tuned) ----
W_C = 0.50
W_A = 0.50
FORMAT_GATE = -1.0
SENSOR_LAYER = 24

# ---- wiring globals, set by the launcher BEFORE trainer.train() ----
MODEL = None            # the live policy model (unsloth 4-bit + LoRA), for_inference
TOKENIZER = None
PROBE = None            # {"scaler":..., "clf":...} frozen v2 sensor
BASELINE_SYSTEM = None  # probe-render system prompt (sensor fit surface)
PERMUTATION = None      # dict row_key->row_key (permuted arm); None => TRUE arm
LOG_PATH = None         # per-step jsonl sink

_lock = threading.Lock()
_p_cache: dict[str, float] = {}   # row_key -> p, valid within a single step
_last_step = -1


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _p_from_state(vec: np.ndarray) -> float:
    score = float(PROBE["clf"].decision_function(
        PROBE["scaler"].transform(vec[None, :]))[0])
    return float(_sigmoid(-score))


def _read_pregen_p(question: str) -> float:
    """Read p at the pre-gen anchor from the LIVE policy — probe-render surface,
    batch-1 prompt-only forward, hidden_states[24] at prompt_len-1. Byte-identical
    to amendment_ai_smoke.pregen_p (the read the smoke proved faithful)."""
    import torch
    from backends import render_probe_prompt
    rendered, _ = render_probe_prompt(TOKENIZER, BASELINE_SYSTEM, question,
                                      enable_thinking=False)
    enc = TOKENIZER(rendered, return_tensors="pt").to(MODEL.device)
    prompt_len = int(enc["input_ids"].shape[1])
    was_training = MODEL.training
    MODEL.eval()
    try:
        with torch.no_grad():
            out = MODEL(**enc, output_hidden_states=True, use_cache=False)
        vec = out.hidden_states[SENSOR_LAYER][0, prompt_len - 1, :].float().cpu().numpy().astype(np.float64)
    finally:
        if was_training:
            MODEL.train()
    return _p_from_state(vec)


def _p_for_row(row_key: str, question: str, question_by_key: dict) -> float:
    """p keyed by row_key, read once per step. Permuted arm: read the policy's OWN
    p for σ(row_key) (marginals preserved, row-level coupling destroyed)."""
    src_key = row_key
    src_question = question
    if PERMUTATION is not None:
        src_key = PERMUTATION.get(row_key, row_key)
        src_question = question_by_key.get(src_key, question)
    if src_key in _p_cache:
        return _p_cache[src_key]
    p = _read_pregen_p(src_question)
    _p_cache[src_key] = p
    return p


def _reset_cache_if_new_step(step: int):
    global _last_step
    if step != _last_step:
        _p_cache.clear()
        _last_step = step


def _expand(values, n):
    return base_reward._expand(values, n)


def par_reward(completions, prompts=None, **kwargs) -> list[float]:
    if MODEL is None or PROBE is None or TOKENIZER is None or BASELINE_SYSTEM is None:
        raise RuntimeError("PAR reward not wired: launcher must set MODEL/TOKENIZER/"
                           "PROBE/BASELINE_SYSTEM before trainer.train().")
    n = len(completions)
    row_keys = _expand(kwargs.get("row_key"), n)
    questions = _expand(kwargs.get("question"), n)
    labels = _expand(kwargs.get("label", "unknown"), n)
    gold_answerable = _expand(kwargs.get("gold_answerable"), n)
    aliases = _expand(kwargs.get("aliases", []), n)
    state = kwargs.get("trainer_state")
    step = int(getattr(state, "global_step", -1)) if state is not None else -1

    question_by_key = {row_keys[i]: questions[i] for i in range(n)}

    with _lock:
        _reset_cache_if_new_step(step)
        rewards: list[float] = []
        log_rows: list[dict[str, Any]] = []
        for i in range(n):
            rk = row_keys[i]
            p = _p_for_row(rk, questions[i], question_by_key)
            text = base_reward._coerce_completion_text(completions[i])
            parsed = base_reward.parse_completion(text)
            refused = base_reward.is_refusal(parsed.answer_text)
            alias_value = aliases[i]
            alias_list = [alias_value] if isinstance(alias_value, str) else list(alias_value or [])
            correct = (False if refused else
                       base_reward.is_correct(parsed.answer_text, alias_list))
            ga = bool(gold_answerable[i]) if gold_answerable[i] is not None \
                else (str(labels[i]) == "known")

            if not parsed.valid_json:
                r = FORMAT_GATE
                r_agree = None; bonus_c = 0.0; bonus_a = 0.0
            else:
                r_agree = p if refused else (1.0 - p)
                bonus_c = W_C if ((not refused) and ga and correct) else 0.0
                bonus_a = W_A if (refused and (not ga)) else 0.0
                r = r_agree + bonus_c + bonus_a
            rewards.append(float(r))
            log_rows.append({
                "step": step, "row_key": rk, "p": round(p, 6),
                "abstained": refused, "correct": correct, "gold_answerable": ga,
                "schema_valid": parsed.valid_json,
                "r_agree": (None if r_agree is None else round(r_agree, 6)),
                "bonus_c": bonus_c, "bonus_a": bonus_a, "reward": round(float(r), 6),
                "permuted": PERMUTATION is not None,
            })
        _log(step, log_rows, rewards, row_keys)
    return rewards


def _log(step: int, log_rows, rewards, row_keys):
    if not LOG_PATH:
        return
    # per-prompt group reward std (the C1 signal) for quick monitoring
    by_key: dict[str, list[float]] = {}
    for rk, rw in zip(row_keys, rewards):
        by_key.setdefault(rk, []).append(rw)
    group_stds = [float(np.std(v)) for v in by_key.values() if len(v) > 1]
    event = {
        "at": datetime.now(timezone.utc).isoformat(), "step": step,
        "n_completions": len(rewards), "n_groups": len(by_key),
        "reward_mean": round(float(np.mean(rewards)), 6),
        "group_std_mean": round(float(np.mean(group_stds)), 6) if group_stds else 0.0,
        "group_std_nonzero_frac": (round(float(np.mean([s > 0 for s in group_stds])), 4)
                                   if group_stds else 0.0),
        "rows": log_rows,
    }
    p = Path(LOG_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
