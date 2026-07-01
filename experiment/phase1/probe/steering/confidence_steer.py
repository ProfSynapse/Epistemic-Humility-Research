#!/usr/bin/env python3
"""Arm A — internal activation steering harness (Paper 5 / confidence-steering experiment).

DESIGN REFERENCE: docs/plans/confidence-steering-experiment.md

NOT authorized for GPU runs. A signed Tier-2 Amendment with locked gates and
explicit user launch approval is required before any real inference run.

Mechanics
---------
At inference time, at a designated decoder layer, we add ``alpha * d`` to the
residual-stream hidden state, where:
  - ``d``     is the unit-norm probe direction (from persist_probe_direction.py)
  - ``alpha`` is a signed steering magnitude, optionally proportional to measured
              uncertainty

Position variants (Paper 5 2×2 design):
  anchor-only  — steer at the SINGLE token that is the pre-answer anchor
                 (prompt's last token, token index = prompt_len - 1)
  all-post     — steer at EVERY token position in the post-answer generation stream

The hook implementation is deliberately separated from model loading so the hook
math is unit-testable on a tiny/synthetic nn.Module without downloading a large
model.

Alpha-proportional steering
---------------------------
Given calibration stats from the direction JSON (positive_mean, negative_mean,
positive_std from the GATE or DIAL), we define:

  uncertainty_scale = (positive_mean - score) / (positive_mean - negative_mean)

clipped to [0, 1], where ``score`` is the current P(positive) for this input
(computed as dot(h, d) mapped through the logistic).  Then:

  effective_alpha = base_alpha * uncertainty_scale

This makes alpha=0 on already-confident inputs and alpha=base_alpha on the most
uncertain ones, avoiding over-hedging on correct-confident responses.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Union

import numpy as np

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Direction loading
# ---------------------------------------------------------------------------

def load_direction(direction_json: Path) -> tuple[np.ndarray, dict]:
    """Load a persisted direction and its metadata.

    Returns
    -------
    d     : float32 numpy array, shape (hidden_dim,), unit-norm
    meta  : the direction JSON dict (layer, calibration, provenance, ...)
    """
    meta = json.loads(direction_json.read_text(encoding="utf-8"))
    st_path = direction_json.with_suffix(".safetensors")
    npy_path = direction_json.with_suffix(".npy")

    d: Optional[np.ndarray] = None
    if st_path.exists():
        try:
            from safetensors.torch import load_file as _st_load
            t = _st_load(str(st_path))
            d = np.asarray(t["d"], dtype=np.float32)
        except ImportError:
            try:
                from safetensors.numpy import load_file as _np_load
                t = _np_load(str(st_path))
                d = np.asarray(t["d"], dtype=np.float32)
            except ImportError:
                pass
    if d is None and npy_path.exists():
        d = np.load(str(npy_path)).astype(np.float32)
    if d is None:
        raise FileNotFoundError(
            f"Direction file not found: tried {st_path} and {npy_path}"
        )

    # Verify unit norm (should be 1.0 within floating-point tolerance)
    norm = float(np.linalg.norm(d))
    if abs(norm - 1.0) > 1e-4:
        raise ValueError(
            f"Direction vector is not unit-norm (norm={norm:.6f}). "
            "Refit with persist_probe_direction.py."
        )
    return d, meta


# ---------------------------------------------------------------------------
# The steering hook (unit-testable on any nn.Module)
# ---------------------------------------------------------------------------

class SteeringHook:
    """Forward hook that adds ``alpha * d`` to the residual stream of one layer.

    Usage
    -----
    Hook is designed to be attached to a SINGLE transformer decoder layer
    (e.g. model.model.layers[best_layer]) via:

        handle = layer.register_forward_hook(hook)

    The hook is position-aware:
      - ``position="anchor"`` — steer only at the single token index stored in
        ``self.anchor_token_idx``; if None, steer at the LAST position.
      - ``position="all_post"`` — steer every position whose index >= anchor_start
        (i.e., in the post-answer generation stream).

    Args
    ----
    d              : unit-norm direction as a torch Tensor (hidden_dim,)
    alpha          : steering magnitude (can be negative to push toward negative class)
    position       : "anchor" | "all_post"
    anchor_token_idx: integer token index to steer at (for "anchor" mode);
                      if None, uses last token; updated externally between calls
    anchor_start   : for "all_post" mode, steer positions >= this index
    verbose        : print steering events (useful for debugging)
    """

    def __init__(
        self,
        d: "torch.Tensor",
        alpha: float = 1.0,
        position: str = "anchor",
        anchor_token_idx: Optional[int] = None,
        anchor_start: Optional[int] = None,
        verbose: bool = False,
    ) -> None:
        if position not in ("anchor", "all_post"):
            raise ValueError(f"position must be 'anchor' or 'all_post', got {position!r}")
        self.d = d  # shape (hidden_dim,)
        self.alpha = alpha
        self.position = position
        self.anchor_token_idx = anchor_token_idx
        self.anchor_start = anchor_start
        self.verbose = verbose
        self._call_count = 0

    def __call__(self, module, input, output):
        """Hook callback: output is (hidden_states, ...) or just hidden_states."""
        self._call_count += 1
        # HuggingFace decoder layers return a tuple; hidden states are [0]
        if isinstance(output, tuple):
            hidden = output[0]  # shape (batch, seq_len, hidden_dim)
            rest = output[1:]
        else:
            hidden = output
            rest = None

        batch, seq_len, hidden_dim = hidden.shape
        d = self.d.to(hidden.device).to(hidden.dtype)

        # Build a mask: which positions get the perturbation
        mask = torch.zeros(seq_len, dtype=torch.bool, device=hidden.device)
        if self.position == "anchor":
            idx = self.anchor_token_idx if self.anchor_token_idx is not None else (seq_len - 1)
            idx = idx % seq_len  # handle negative indexing
            mask[idx] = True
        elif self.position == "all_post":
            start = self.anchor_start if self.anchor_start is not None else 0
            mask[start:] = True

        n_steered = int(mask.sum().item())
        if n_steered > 0:
            # hidden[batch, positions_to_steer, :] += alpha * d
            hidden = hidden.clone()
            hidden[:, mask, :] = hidden[:, mask, :] + self.alpha * d.unsqueeze(0)
            if self.verbose:
                print(f"[SteeringHook] call={self._call_count} "
                      f"steered {n_steered} positions, alpha={self.alpha:.4f}",
                      flush=True)

        if rest is not None:
            return (hidden,) + rest
        return hidden


# ---------------------------------------------------------------------------
# Alpha computation
# ---------------------------------------------------------------------------

def compute_proportional_alpha(
    base_alpha: float,
    score: float,
    calibration: dict,
) -> float:
    """Compute alpha proportional to measured uncertainty.

    Parameters
    ----------
    base_alpha  : maximum alpha (applied when uncertainty is maximum)
    score       : current P(positive) for this input, e.g. from dot(h, d) + logistic
    calibration : dict from direction JSON with positive_mean, negative_mean keys

    Returns
    -------
    effective_alpha in [0, base_alpha]
    """
    pos_mean = calibration.get("positive_mean", 1.0)
    neg_mean = calibration.get("negative_mean", 0.0)
    denom = pos_mean - neg_mean
    if abs(denom) < 1e-6:
        return base_alpha  # degenerate — use base
    uncertainty_scale = (pos_mean - score) / denom
    uncertainty_scale = float(np.clip(uncertainty_scale, 0.0, 1.0))
    return base_alpha * uncertainty_scale


# ---------------------------------------------------------------------------
# Model loader (reuses Amendment X pattern: multimodal fallback, dtype kwarg)
# ---------------------------------------------------------------------------

def load_model_and_tokenizer(model_name: str, device: str = "cpu"):
    """Load model + tokenizer with the Amendment X backward-compatible recipe.

    Tries AutoModelForCausalLM first, then multimodal fallbacks.
    Handles transformers 5.x dtype kwarg rename (torch_dtype -> dtype).
    CPU-safe: caller passes device="cpu" for unit tests; GPU callers pass "cuda".

    NOTE: For real GPU runs, the Amendment Z extractor already has the canonical
    version of this loader. Use this for the steer harness which needs the same
    model object.
    """
    if not _TORCH_AVAILABLE:
        raise ImportError("torch is required for model loading")

    import transformers as _tf
    _major = int(_tf.__version__.split(".")[0])
    _dtype_kw = "dtype" if _major >= 5 else "torch_dtype"
    load_kw = {_dtype_kw: torch.bfloat16, "device_map": device}

    model = None
    last_err = None
    _classes = ["AutoModelForCausalLM"]
    for _name in ("AutoModelForImageTextToText", "AutoModelForVision2Seq"):
        if hasattr(_tf, _name):
            _classes.append(_name)

    for _cls_name in _classes:
        try:
            _Cls = getattr(_tf, _cls_name)
            model = _Cls.from_pretrained(model_name, **load_kw)
            print(f"[confidence_steer] loaded via {_cls_name}", flush=True)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e

    if model is None:
        raise RuntimeError(
            f"Could not load {model_name} via any of {_classes}: {last_err}"
        )

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.eval()
    return model, tokenizer


# ---------------------------------------------------------------------------
# Hook registration helper
# ---------------------------------------------------------------------------

def get_decoder_layer(model, layer_idx: int):
    """Return the decoder layer module for hook registration.

    Handles different model architectures:
      - model.model.layers[i]  (LLaMA / Qwen3 / Ministral / most transformers)
      - model.language_model.model.layers[i]  (some multimodal wrappers)
      - model.model.decoder.layers[i]  (OPT-style)
    """
    # Try common patterns in order
    for attr_path in (
        ["model", "layers"],
        ["language_model", "model", "layers"],
        ["model", "decoder", "layers"],
        ["transformer", "h"],  # GPT-2 style
    ):
        obj = model
        try:
            for attr in attr_path:
                obj = getattr(obj, attr)
            if hasattr(obj, "__getitem__"):
                return obj[layer_idx]
        except AttributeError:
            continue
    raise AttributeError(
        f"Cannot find decoder layers on model of type {type(model).__name__}. "
        "Add a custom path in get_decoder_layer()."
    )


def register_steering_hook(
    model,
    direction_path: Path,
    alpha: float = 1.0,
    position: str = "anchor",
    anchor_token_idx: Optional[int] = None,
    anchor_start: Optional[int] = None,
    verbose: bool = False,
) -> tuple["SteeringHook", object]:
    """Load direction, build hook, register on the target layer.

    Returns
    -------
    hook   : SteeringHook instance (can update .alpha, .anchor_token_idx externally)
    handle : the hook handle (call handle.remove() to deregister)
    """
    if not _TORCH_AVAILABLE:
        raise ImportError("torch is required for hook registration")

    d_np, meta = load_direction(direction_path)
    layer_idx = meta["best_layer"]

    d_tensor = torch.from_numpy(d_np)  # float32
    hook = SteeringHook(
        d=d_tensor,
        alpha=alpha,
        position=position,
        anchor_token_idx=anchor_token_idx,
        anchor_start=anchor_start,
        verbose=verbose,
    )
    layer = get_decoder_layer(model, layer_idx)
    handle = layer.register_forward_hook(hook)
    print(f"[confidence_steer] hook registered at layer {layer_idx} "
          f"position={position} alpha={alpha:.4f}", flush=True)
    return hook, handle


# ---------------------------------------------------------------------------
# Alpha sweep helper
# ---------------------------------------------------------------------------

def alpha_sweep(
    alpha_values: list[float],
    generate_fn,
    update_alpha_fn,
) -> list[dict]:
    """Run generation at each alpha value and collect results.

    Parameters
    ----------
    alpha_values  : list of alpha floats to try
    generate_fn   : callable(alpha) -> dict of generation outputs
    update_alpha_fn : callable(alpha) -> None (updates hook.alpha in place)

    Returns
    -------
    list of dicts: [{alpha: float, **generation_outputs}]
    """
    results = []
    for alpha in alpha_values:
        update_alpha_fn(alpha)
        out = generate_fn(alpha)
        results.append({"alpha": alpha, **out})
    return results


# ---------------------------------------------------------------------------
# CLI (for inspection / dry-run only — actual GPU runs need the amendment)
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True,
                    help="Model name/path (HF hub or local)")
    ap.add_argument("--direction", required=True, type=Path,
                    help="Path to direction_<signal>.json (sibling .safetensors loaded automatically)")
    ap.add_argument("--alpha", type=float, default=1.0,
                    help="Steering magnitude")
    ap.add_argument("--position", choices=["anchor", "all_post"], default="anchor",
                    help="Which positions to steer")
    ap.add_argument("--prompt", default="What is the capital of France?",
                    help="Test prompt (dry-run mode only)")
    ap.add_argument("--device", default="cpu",
                    help="Device for loading (cpu for smoke test; cuda for real runs)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Load model + register hook + print config without generating")
    a = ap.parse_args(argv)

    if not _TORCH_AVAILABLE:
        print("[confidence_steer] ERROR: torch not available", flush=True)
        return 1

    print(f"[confidence_steer] loading direction from {a.direction} ...", flush=True)
    d_np, meta = load_direction(a.direction)
    print(f"[confidence_steer] direction: layer={meta['best_layer']} "
          f"model={meta.get('provenance', {}).get('model_tag', '?')} "
          f"norm={np.linalg.norm(d_np):.6f}", flush=True)

    if a.dry_run:
        print("[confidence_steer] dry-run: direction loaded OK, skipping model load",
              flush=True)
        return 0

    print(f"[confidence_steer] loading model {a.model} ...", flush=True)
    model, tokenizer = load_model_and_tokenizer(a.model, device=a.device)

    hook, handle = register_steering_hook(
        model=model,
        direction_path=a.direction,
        alpha=a.alpha,
        position=a.position,
        verbose=True,
    )
    print(f"[confidence_steer] registered hook at layer={meta['best_layer']} "
          f"position={a.position} alpha={a.alpha}", flush=True)

    # Smoke: one forward pass
    enc = tokenizer(a.prompt, return_tensors="pt")
    with torch.no_grad():
        gen = model.generate(**enc, max_new_tokens=32, do_sample=False)
    out_text = tokenizer.decode(gen[0], skip_special_tokens=True)
    print(f"[confidence_steer] output: {out_text!r}", flush=True)
    handle.remove()
    return 0


if __name__ == "__main__":
    sys.exit(main())
