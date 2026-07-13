"""Shared model/hook/loader machinery, reused for H3
snap-seed-sampled-decode-replication.

Copied verbatim (not imported cross-experiment per this repo's own
convention) from `experiments/doubt-gated-caution-tighten/model_lib.py`,
plus three additions local to this experiment (the resolved cell never
needed a Wilson-CI overlap test or a per-seed placebo redraw):
`wilson_ci_overlap`, `draw_random_direction`, `draw_permuted_gate_indices`.
Everything above the "H3-local additions" marker is unchanged from the
resolved cell; do not edit it here without updating the source copy too.

That module's own docstring (preserved below):

Ported (logic, not import) from the sibling two-signal experiment's
`analysis/gate_snap_lib.py` (worktree
`/home/profsynapse/code/ehr-worktrees/two-signal`, branch
`exp/two-signal-caution-regulation-instruct`, read in full before writing
this): uses the tuner's own InterventionHook / GenerationInterventionController
unmodified. Does NOT modify synaptic-tuner.

FIXED absolute-realized-projection dosing: given a target realized readback T
(the SNAP setpoint s*), the commanded gain is strength = T / sigma_c, since
the tuner's erase_write law writes setpoint = gain * sigma exactly
(synaptic-tuner MechInterp/intervention/hooks.py:erase_and_write) and
hook.last_readback confirms the realized value at run time (never assumed).
"""

from __future__ import annotations

import json
import random as pyrandom
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent  # experiment dir
TUNER_DIR = HERE.parent.parent / "synaptic-tuner"
RENDER_DIR = HERE.parent / "common" / "renders"

for p in (str(TUNER_DIR), str(RENDER_DIR), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from MechInterp.intervention import (  # noqa: E402
    InterventionHook,
    GenerationInterventionController,
    get_decoder_layer,
)
from MechInterp.probe import load_frozen_direction  # noqa: E402
from ah_a0_raw_base_render import render  # noqa: E402,F401  (re-exported)

MODEL_NAME = "unsloth/Qwen3-4B"


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def load_model():
    """Plain HF loading (NOT unsloth): unsloth's fused inference path does
    not reliably fire per-decode-step forward hooks (see the sibling
    experiment's dose_escalation_bf16_ambient_relative.py docstring)."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, device_map="auto", dtype=torch.bfloat16
    )
    model.eval()
    return model, tokenizer


def setup_hook_from_path(direction_path: Path):
    direction_record = load_frozen_direction(str(direction_path))
    direction = torch.tensor(direction_record["vector_np"], dtype=torch.float32)
    sigma = float(direction_record.get("sigma", 1.0))
    layer_idx = int(direction_record["layer"])
    hook = InterventionHook(
        law="erase_write", direction=direction, sigma=sigma,
        position="anchor_onward", measure_readback=True,
    )
    controller = GenerationInterventionController(hook)
    return hook, controller, layer_idx, sigma, direction_record


def setup_hook_from_vector(vector, sigma: float, layer_idx: int):
    """Same as setup_hook_from_path but takes a raw (possibly random)
    direction vector directly -- used by the G3(i) random-direction placebo,
    which is not a committed direction JSON."""
    direction = torch.tensor(vector, dtype=torch.float32)
    hook = InterventionHook(
        law="erase_write", direction=direction, sigma=sigma,
        position="anchor_onward", measure_readback=True,
    )
    controller = GenerationInterventionController(hook)
    return hook, controller, layer_idx, sigma


def wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float, float]:
    """Wilson score 95% CI for a binomial proportion. Returns (point, lo, hi)."""
    if n == 0:
        return 0.0, 0.0, 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return phat, max(0.0, center - half), min(1.0, center + half)


# ---------------------------------------------------------------------------
# H3-local additions.
# ---------------------------------------------------------------------------

def wilson_ci_overlap(ci_a: tuple[float, float], ci_b: tuple[float, float]) -> bool:
    """True iff two closed intervals [lo, hi] overlap (share at least one
    point). Used by H3-G0's "wilson_ci overlaps [0.667, 0.793]" clause."""
    a_lo, a_hi = ci_a
    b_lo, b_hi = ci_b
    return a_lo <= b_hi and b_lo <= a_hi


def draw_random_direction(seed: int, hidden_dim: int = 2560) -> np.ndarray:
    """Fresh unit random direction for one H3-G3 seed, using the SAME method
    as the resolved cell's own build_random_direction.py
    (np.random.RandomState(seed).normal(size=hidden_dim), unit-normalized),
    just re-seeded per H3 seed instead of the single committed 20260707."""
    rng = np.random.RandomState(seed)
    v = rng.normal(size=hidden_dim)
    return v / np.linalg.norm(v)


def draw_permuted_gate_indices(pool_size: int, n_fired: int, seed: int) -> set[int]:
    """Fresh permuted-gate assignment for one H3-G3 seed: n_fired indices
    chosen uniformly at random (without replacement) from range(pool_size),
    using the SAME method as the resolved cell's own pipeline.py permuted_gate
    placebo (pyrandom.Random(seed).shuffle then take the first n_fired), just
    re-seeded per H3 seed instead of the single committed 20260707."""
    rng = pyrandom.Random(seed)
    idx = list(range(pool_size))
    rng.shuffle(idx)
    return set(idx[:n_fired])
