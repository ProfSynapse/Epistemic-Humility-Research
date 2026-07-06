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
        ``self.anchor_token_idx``; if None, steer at the LAST position. Applies
        the SAME index to every batch row (no padding awareness) — correct for
        a single left-padded prefill where the anchor is a shared offset, kept
        for backward compatibility.
      - ``position="all_post"`` — steer every position whose index >= anchor_start
        (i.e., in the post-answer generation stream).
      - ``position="final"`` — steer ONLY each batch row's true last non-pad
        token. The per-row final index is taken from ``self.final_positions``
        (a length-`batch` sequence of ints, set externally from the batch's
        attention mask); if that is None, the hook derives it from
        ``self.attention_mask`` ((batch, seq_len), 1 = real token) handling both
        left and right padding; if BOTH are None it falls back to the last
        position of every row (the no-padding batch-of-1 / already-trimmed case).

    Per-element alpha
    -----------------
    ``alpha`` may be a Python float (one magnitude for the whole batch, the
    original contract) OR a per-batch-element vector of length `batch` (a list,
    numpy array, or 1-D torch tensor). A vector is broadcast so row ``b`` is
    shifted by ``alpha[b] * d`` at its steered positions; a scalar behaves
    exactly as before. This lets the caller pass compute_proportional_alpha's
    per-row effective alphas in a single batched forward.

    Args
    ----
    d              : unit-norm direction as a torch Tensor (hidden_dim,)
    alpha          : steering magnitude — scalar (all rows) or length-`batch`
                     vector (per row). Negative pushes toward the negative class.
    position       : "anchor" | "all_post" | "final"
    anchor_token_idx: integer token index to steer at (for "anchor" mode);
                      if None, uses last token; updated externally between calls
    anchor_start   : for "all_post" mode, steer positions >= this index
    final_positions: for "final" mode, per-row last-non-pad token indices
                     (length `batch`); set externally between calls
    attention_mask : for "final" mode, (batch, seq_len) mask (1 = real token)
                     used to derive per-row final positions when
                     final_positions is None; set externally between calls
    verbose        : print steering events (useful for debugging)
    """

    def __init__(
        self,
        d: "torch.Tensor",
        alpha: Union[float, "torch.Tensor", list, np.ndarray] = 1.0,
        position: str = "anchor",
        anchor_token_idx: Optional[int] = None,
        anchor_start: Optional[int] = None,
        final_positions: Optional[Union["torch.Tensor", list, np.ndarray]] = None,
        attention_mask: Optional["torch.Tensor"] = None,
        verbose: bool = False,
    ) -> None:
        if position not in ("anchor", "all_post", "final"):
            raise ValueError(
                "position must be 'anchor', 'all_post', or 'final', "
                f"got {position!r}")
        self.d = d  # shape (hidden_dim,)
        self.alpha = alpha
        self.position = position
        self.anchor_token_idx = anchor_token_idx
        self.anchor_start = anchor_start
        self.final_positions = final_positions
        self.attention_mask = attention_mask
        self.verbose = verbose
        self._call_count = 0

    # -- per-row final-position resolution ---------------------------------

    def _resolve_final_positions(self, batch: int, seq_len: int,
                                 device) -> "torch.Tensor":
        """Return a length-`batch` LongTensor of last-non-pad indices per row.

        Priority: explicit self.final_positions > derived from
        self.attention_mask > last position of every row (no-padding fallback).
        A negative index is wrapped modulo seq_len (parity with anchor mode).
        """
        if self.final_positions is not None:
            pos = torch.as_tensor(self.final_positions, device=device,
                                  dtype=torch.long).reshape(-1)
            if pos.numel() != batch:
                raise ValueError(
                    f"final_positions has length {pos.numel()}, expected "
                    f"batch={batch}")
            return pos % seq_len
        if self.attention_mask is not None:
            am = torch.as_tensor(self.attention_mask, device=device)
            if am.shape[0] != batch:
                raise ValueError(
                    f"attention_mask batch dim {am.shape[0]} != hidden batch "
                    f"{batch}")
            # Last index where the mask is 1, per row. Works for left AND right
            # padding: argmax over reversed row finds the last real token.
            am_bool = am.to(torch.bool)
            seq = am_bool.shape[1]
            flipped = torch.flip(am_bool.to(torch.int64), dims=[1])
            # first real token from the right -> convert back to a forward index
            last_from_right = torch.argmax(flipped, dim=1)
            pos = (seq - 1) - last_from_right
            # a fully-padded row (no real token) has no final position; clamp to
            # the last index rather than steer a pad (degenerate, should not occur)
            has_real = am_bool.any(dim=1)
            pos = torch.where(has_real, pos, torch.full_like(pos, seq - 1))
            return pos
        # No padding info: every row's last position.
        return torch.full((batch,), seq_len - 1, dtype=torch.long,
                          device=device)

    def _alpha_per_row(self, batch: int, device, dtype) -> "torch.Tensor":
        """Return a length-`batch` alpha tensor (scalar alpha broadcast)."""
        a = self.alpha
        if isinstance(a, (int, float)):
            return torch.full((batch,), float(a), device=device, dtype=dtype)
        a = torch.as_tensor(a, device=device, dtype=dtype).reshape(-1)
        if a.numel() == 1:
            return a.expand(batch)
        if a.numel() != batch:
            raise ValueError(
                f"alpha vector has length {a.numel()}, expected batch={batch} "
                "(or a scalar)")
        return a

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
        alpha_row = self._alpha_per_row(batch, hidden.device, hidden.dtype)

        if self.position == "final":
            # Per-row edit at each row's true last non-pad token. A shared
            # position mask cannot express different indices per row, so edit
            # rows in one gather/scatter instead.
            final_pos = self._resolve_final_positions(batch, seq_len,
                                                       hidden.device)
            active = alpha_row != 0.0
            n_steered = int(active.sum().item())
            if n_steered > 0:
                hidden = hidden.clone()
                rows = torch.arange(batch, device=hidden.device)[active]
                cols = final_pos[active]
                delta = alpha_row[active].unsqueeze(1) * d.unsqueeze(0)
                hidden[rows, cols, :] = hidden[rows, cols, :] + delta
            if self.verbose:
                print(f"[SteeringHook] call={self._call_count} position=final "
                      f"steered {n_steered}/{batch} rows at per-row last tokens",
                      flush=True)
            if rest is not None:
                return (hidden,) + rest
            return hidden

        # Shared-position modes: same steered columns for every batch row.
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
            # hidden[batch, positions_to_steer, :] += alpha_row * d, with
            # alpha_row broadcast over positions and hidden_dim.
            hidden = hidden.clone()
            add = alpha_row.view(batch, 1, 1) * d.view(1, 1, hidden_dim)
            hidden[:, mask, :] = hidden[:, mask, :] + add
            if self.verbose:
                a = self.alpha
                a_str = (f"{float(a):.4f}" if isinstance(a, (int, float))
                         else f"vector[{batch}]")
                print(f"[SteeringHook] call={self._call_count} "
                      f"steered {n_steered} positions, alpha={a_str}",
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

def load_model_and_tokenizer(model_name: str, device: str = "cpu",
                             adapter: Optional[str] = None,
                             adapter_revision: Optional[str] = None):
    """Load model + tokenizer with the Amendment X backward-compatible recipe.

    Tries AutoModelForCausalLM first, then multimodal fallbacks.
    Handles transformers 5.x dtype kwarg rename (torch_dtype -> dtype).
    CPU-safe: caller passes device="cpu" for unit tests; GPU callers pass "cuda".

    NOTE: For real GPU runs, the Amendment Z extractor already has the canonical
    version of this loader. Use this for the steer harness which needs the same
    model object.

    Adapter (LoRA) support
    ----------------------
    When ``adapter`` is given, a PEFT LoRA adapter is applied on top of the base
    with ``PeftModel.from_pretrained(model, adapter, revision=adapter_revision)``
    — the same attach path the AK/AL/AG extraction harnesses use for the
    deployed clean-SFT->GRPO-v2 lineage (base = the merged-16bit clean-SFT model,
    adapter = the trained grpo-v2 LoRA at a pinned revision). Leave ``adapter``
    None (the default) for the raw single-checkpoint path; every existing call
    site is unaffected.
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

    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter,
                                          revision=adapter_revision)
        print(f"[confidence_steer] attached adapter {adapter}"
              f"@{adapter_revision}", flush=True)

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
      - PEFT-wrapped models (PeftModelForCausalLM) are unwrapped first
    """
    # PEFT wraps the causal-LM as PeftModelForCausalLM -> LoraModel -> base;
    # unwrap so the attribute probes below see the real architecture.
    if hasattr(model, "get_base_model"):
        model = model.get_base_model()
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
