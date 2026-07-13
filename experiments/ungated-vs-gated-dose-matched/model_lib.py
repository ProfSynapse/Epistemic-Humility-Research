"""Shared model/hook/loader machinery, reused for H4 ungated-vs-gated-dose-matched.

Copied verbatim (not imported cross-experiment per this repo's own
convention) from `experiments/doubt-gated-caution-tighten/model_lib.py`, plus
one addition local to this experiment: `mcnemar_exact`, the paired test
H4-G1 needs and the resolved cell never required (it had no paired-arm
contrast). Everything above that line is unchanged from the resolved cell;
do not edit it here without updating the source copy too.

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
import math
import sys
from pathlib import Path

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
# H4-local addition: exact paired McNemar test, no scipy dependency.
# ---------------------------------------------------------------------------

def mcnemar_exact(b: int, c: int) -> dict:
    """Exact two-sided McNemar test on the discordant pair counts.

    b = n(arm_a=1, arm_b=0), c = n(arm_a=0, arm_b=1) -- the two cells of the
    2x2 paired table that disagree. Concordant pairs (both 0 or both 1)
    carry no information for McNemar and are not passed in. Under the null
    (marginal homogeneity), the discordant total n = b + c is split
    Binomial(n, 0.5); the exact two-sided p-value is
    2 * min(P(X <= min(b,c)), P(X >= max(b,c))), capped at 1.0, computed via
    math.comb (no scipy dependency; exact for any n, no normal-approximation
    error at the small-to-moderate discordant counts this experiment sees).
    """
    n = b + c
    if n == 0:
        return {"b": b, "c": c, "n_discordant": 0, "statistic": None, "p_value": 1.0}
    k = min(b, c)
    # P(X <= k) for X ~ Binomial(n, 0.5), computed exactly as a dyadic ratio.
    cum = sum(math.comb(n, i) for i in range(0, k + 1))
    p_le_k = cum / (2 ** n)
    p_value = min(1.0, 2 * p_le_k)
    return {
        "b": b, "c": c, "n_discordant": n,
        "statistic": ((abs(b - c) - 1) ** 2 / n) if n > 0 else None,  # continuity-corrected chi2, reported only
        "p_value": p_value,
    }
