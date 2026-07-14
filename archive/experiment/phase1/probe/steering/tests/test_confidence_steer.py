"""Unit tests for confidence_steer.py

Tests (b) from the spec:
  The steering hook actually shifts the target layer's activation by exactly alpha * d
  (measure before/after).

Uses a tiny synthetic nn.Module — no large model downloads.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pytest

torch = pytest.importorskip("torch", reason="torch required for steer hook tests")
import torch.nn as nn


# ---------------------------------------------------------------------------
# Tiny synthetic module for hook testing
# ---------------------------------------------------------------------------

class TinyDecoder(nn.Module):
    """Minimal decoder block: LayerNorm -> Linear, returns (hidden,) tuple.

    Emulates the output structure of a HuggingFace decoder layer:
    forward() returns a tuple (hidden_states, ...) where hidden_states has
    shape (batch, seq_len, hidden_dim).
    """
    def __init__(self, hidden_dim: int = 32):
        super().__init__()
        self.norm = nn.LayerNorm(hidden_dim)
        self.linear = nn.Linear(hidden_dim, hidden_dim, bias=False)
        nn.init.eye_(self.linear.weight)  # identity init so output == input

    def forward(self, x):
        h = self.norm(x)
        h = self.linear(h)
        return (h,)  # HuggingFace-style: return tuple


class TinyModel(nn.Module):
    """Tiny model with a single decoder layer, for hook registration testing."""
    def __init__(self, hidden_dim: int = 32, n_layers: int = 3):
        super().__init__()
        self.model = nn.ModuleDict({
            "layers": nn.ModuleList([TinyDecoder(hidden_dim) for _ in range(n_layers)])
        })

    def forward(self, x):
        h = x
        for layer in self.model["layers"]:
            out = layer(h)
            h = out[0]
        return h


# ---------------------------------------------------------------------------
# Hook unit tests
# ---------------------------------------------------------------------------

class TestSteeringHookAnchorMode:
    """Test (b): hook shifts EXACTLY the anchor position by alpha * d."""

    @pytest.fixture
    def setup(self):
        from confidence_steer import SteeringHook
        batch, seq_len, hidden_dim = 1, 8, 32
        alpha = 2.5
        d_np = np.random.default_rng(0).standard_normal(hidden_dim).astype(np.float32)
        d_np /= np.linalg.norm(d_np)  # unit norm
        d_tensor = torch.from_numpy(d_np)
        anchor_idx = 3

        hook = SteeringHook(
            d=d_tensor,
            alpha=alpha,
            position="anchor",
            anchor_token_idx=anchor_idx,
        )
        return hook, d_np, d_tensor, alpha, anchor_idx, hidden_dim, seq_len

    def test_hook_shifts_anchor_position(self, setup):
        """The hidden state at anchor_idx must shift by exactly alpha * d."""
        from confidence_steer import SteeringHook
        hook, d_np, d_tensor, alpha, anchor_idx, hidden_dim, seq_len = setup

        batch = 1
        x = torch.zeros(batch, seq_len, hidden_dim)
        x_before = x[:, anchor_idx, :].clone().numpy()

        module_stub = nn.Linear(1, 1)  # dummy module (not used by hook math)
        output_tuple = (x.clone(),)
        result = hook(module_stub, None, output_tuple)
        h_out = result[0]

        x_after = h_out[:, anchor_idx, :].detach().numpy()
        expected_shift = alpha * d_np
        actual_shift = (x_after - x_before)[0]
        np.testing.assert_allclose(
            actual_shift, expected_shift, atol=1e-5,
            err_msg="Anchor position not shifted by exactly alpha * d"
        )

    def test_hook_does_not_shift_other_positions(self, setup):
        """Non-anchor positions must NOT be shifted."""
        from confidence_steer import SteeringHook
        hook, d_np, d_tensor, alpha, anchor_idx, hidden_dim, seq_len = setup

        batch = 1
        x = torch.zeros(batch, seq_len, hidden_dim)
        x_orig = x.clone()

        module_stub = nn.Linear(1, 1)
        output_tuple = (x.clone(),)
        result = hook(module_stub, None, output_tuple)
        h_out = result[0].detach()

        for pos in range(seq_len):
            if pos == anchor_idx:
                continue
            diff = (h_out[:, pos, :] - x_orig[:, pos, :]).abs().max().item()
            assert diff < 1e-6, \
                f"Position {pos} (non-anchor) was shifted by {diff:.2e} (should be 0)"

    def test_hook_respects_alpha_scaling(self, setup):
        """Doubling alpha should double the shift."""
        from confidence_steer import SteeringHook
        hook, d_np, d_tensor, alpha, anchor_idx, hidden_dim, seq_len = setup

        batch = 1
        x_base = torch.zeros(batch, seq_len, hidden_dim)

        # Apply with alpha
        hook.alpha = alpha
        r1 = hook(nn.Linear(1, 1), None, (x_base.clone(),))[0]
        shift1 = (r1[:, anchor_idx, :] - x_base[:, anchor_idx, :]).detach().numpy()

        # Apply with 2 * alpha
        hook.alpha = 2 * alpha
        r2 = hook(nn.Linear(1, 1), None, (x_base.clone(),))[0]
        shift2 = (r2[:, anchor_idx, :] - x_base[:, anchor_idx, :]).detach().numpy()

        np.testing.assert_allclose(
            shift2, 2 * shift1, atol=1e-5,
            err_msg="Doubling alpha did not double the shift"
        )

    def test_hook_works_on_last_position_when_anchor_idx_is_none(self):
        """When anchor_token_idx is None, last position is steered."""
        from confidence_steer import SteeringHook
        hidden_dim, seq_len = 16, 5
        d = torch.ones(hidden_dim) / (hidden_dim ** 0.5)
        alpha = 1.0
        hook = SteeringHook(d=d, alpha=alpha, position="anchor", anchor_token_idx=None)

        x = torch.zeros(1, seq_len, hidden_dim)
        result = hook(nn.Linear(1, 1), None, (x.clone(),))[0].detach()

        last_shift = (result[:, -1, :] - x[:, -1, :]).abs().max().item()
        other_shifts = [(result[:, i, :] - x[:, i, :]).abs().max().item()
                        for i in range(seq_len - 1)]

        assert last_shift > 1e-6, "Last position should be shifted when anchor_idx is None"
        for i, shift in enumerate(other_shifts):
            assert shift < 1e-6, \
                f"Position {i} should not be shifted; got {shift:.2e}"


class TestSteeringHookAllPostMode:
    """Test all_post position variant: all positions >= anchor_start are steered."""

    def test_all_post_steers_all_positions_from_start(self):
        from confidence_steer import SteeringHook
        hidden_dim, seq_len = 16, 8
        anchor_start = 3
        d = torch.ones(hidden_dim) / (hidden_dim ** 0.5)
        alpha = 1.0
        hook = SteeringHook(
            d=d, alpha=alpha, position="all_post", anchor_start=anchor_start
        )

        x = torch.zeros(1, seq_len, hidden_dim)
        result = hook(nn.Linear(1, 1), None, (x.clone(),))[0].detach()

        for pos in range(seq_len):
            shift = (result[:, pos, :] - x[:, pos, :]).abs().max().item()
            if pos >= anchor_start:
                assert shift > 1e-6, \
                    f"Position {pos} >= anchor_start={anchor_start} should be steered; shift={shift:.2e}"
            else:
                assert shift < 1e-6, \
                    f"Position {pos} < anchor_start={anchor_start} should NOT be steered; shift={shift:.2e}"

    def test_all_post_with_zero_start_steers_all(self):
        from confidence_steer import SteeringHook
        hidden_dim, seq_len = 8, 4
        d = torch.zeros(hidden_dim)
        d[0] = 1.0  # unit vector along dim 0
        hook = SteeringHook(d=d, alpha=0.5, position="all_post", anchor_start=0)

        x = torch.zeros(1, seq_len, hidden_dim)
        result = hook(nn.Linear(1, 1), None, (x.clone(),))[0].detach()

        for pos in range(seq_len):
            shift = result[0, pos, 0].item()
            assert abs(shift - 0.5) < 1e-5, \
                f"Position {pos}: expected shift 0.5 (alpha * d[0]), got {shift:.4f}"


class TestSteeringHookExactShift:
    """Integration: test that hook + TinyModel produces exactly alpha * d shift at target layer."""

    def test_hook_on_tiny_model_shifts_output(self):
        """Register hook on layer 1 of TinyModel; verify the output changes by alpha*d."""
        from confidence_steer import SteeringHook, get_decoder_layer

        hidden_dim = 32
        seq_len = 4
        alpha = 1.0
        anchor_idx = 2

        model = TinyModel(hidden_dim=hidden_dim, n_layers=3)
        model.eval()

        d_np = np.zeros(hidden_dim, dtype=np.float32)
        d_np[0] = 1.0  # unit vector along dim 0
        d_tensor = torch.from_numpy(d_np)

        hook = SteeringHook(
            d=d_tensor,
            alpha=alpha,
            position="anchor",
            anchor_token_idx=anchor_idx,
        )

        target_layer = get_decoder_layer(model, 1)

        # Forward pass WITHOUT hook
        x = torch.randn(1, seq_len, hidden_dim)
        with torch.no_grad():
            out_no_hook = model(x)

        # Register hook and forward pass WITH hook
        handle = target_layer.register_forward_hook(hook)
        with torch.no_grad():
            out_with_hook = model(x)
        handle.remove()

        # The output differs — the hook injected at layer 1's anchor position
        diff = (out_with_hook - out_no_hook).abs().max().item()
        assert diff > 1e-6, \
            "Hook registered but output did not change — hook may not be attached correctly"


class TestProportionalAlpha:
    """Test compute_proportional_alpha logic."""

    def test_max_uncertainty_gives_base_alpha(self):
        from confidence_steer import compute_proportional_alpha
        cal = {"positive_mean": 0.8, "negative_mean": 0.2}
        # score == negative_mean => maximum uncertainty => alpha == base_alpha
        result = compute_proportional_alpha(2.0, 0.2, cal)
        assert abs(result - 2.0) < 1e-6, f"Expected base_alpha=2.0, got {result}"

    def test_confident_gives_zero_alpha(self):
        from confidence_steer import compute_proportional_alpha
        cal = {"positive_mean": 0.8, "negative_mean": 0.2}
        # score == positive_mean => already confident => alpha == 0
        result = compute_proportional_alpha(2.0, 0.8, cal)
        assert abs(result) < 1e-6, f"Expected alpha~0, got {result}"

    def test_midpoint_gives_half_alpha(self):
        from confidence_steer import compute_proportional_alpha
        cal = {"positive_mean": 0.8, "negative_mean": 0.2}
        mid = 0.5  # midpoint between 0.2 and 0.8
        result = compute_proportional_alpha(2.0, mid, cal)
        assert abs(result - 1.0) < 1e-4, f"Expected half of base_alpha=1.0, got {result}"

    def test_clip_to_zero(self):
        from confidence_steer import compute_proportional_alpha
        cal = {"positive_mean": 0.8, "negative_mean": 0.2}
        # score above positive_mean => over-confident => clip to 0
        result = compute_proportional_alpha(2.0, 0.95, cal)
        assert result == 0.0, f"Expected clipped to 0.0, got {result}"

    def test_clip_to_base_alpha(self):
        from confidence_steer import compute_proportional_alpha
        cal = {"positive_mean": 0.8, "negative_mean": 0.2}
        # score below negative_mean => clip to base_alpha
        result = compute_proportional_alpha(2.0, 0.05, cal)
        assert result == 2.0, f"Expected clipped to base_alpha=2.0, got {result}"


class TestLoadDirection:
    """Test load_direction with a synthetic safetensors file."""

    def test_load_direction_from_fixture(self, tiny_direction_dir):
        from confidence_steer import load_direction
        path = tiny_direction_dir / "direction_gate.json"
        d, meta = load_direction(path)
        assert isinstance(d, np.ndarray), "d must be numpy array"
        assert d.dtype == np.float32, f"d.dtype must be float32, got {d.dtype}"
        norm = float(np.linalg.norm(d))
        assert abs(norm - 1.0) < 1e-4, f"Loaded direction not unit-norm: {norm:.6f}"

    def test_load_direction_meta_has_best_layer(self, tiny_direction_dir):
        from confidence_steer import load_direction
        path = tiny_direction_dir / "direction_dial.json"
        _, meta = load_direction(path)
        assert "best_layer" in meta, "meta must have best_layer"
        assert isinstance(meta["best_layer"], int)
