"""Unit tests for persist_probe_direction.py

Tests (a) from the spec:
  persist_probe_direction produces a unit-norm direction + sane layer + calibration
  from the synthetic fixture.

All tests are CPU-only. No model downloads.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_direction_json(direction_dir: Path, signal: str) -> dict:
    path = direction_dir / f"direction_{signal}.json"
    assert path.exists(), f"direction_{signal}.json not found in {direction_dir}"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_direction_vector(direction_dir: Path, signal: str) -> np.ndarray:
    """Load direction vector from safetensors or npy fallback."""
    st_path = direction_dir / f"direction_{signal}.safetensors"
    npy_path = direction_dir / f"direction_{signal}.npy"

    if st_path.exists():
        if _TORCH_AVAILABLE:
            try:
                from safetensors.torch import load_file
                t = load_file(str(st_path))
                return np.asarray(t["d"], dtype=np.float32)
            except ImportError:
                pass
        try:
            from safetensors.numpy import load_file
            t = load_file(str(st_path))
            return np.asarray(t["d"], dtype=np.float32)
        except ImportError:
            pass
    if npy_path.exists():
        return np.load(str(npy_path)).astype(np.float32)
    raise FileNotFoundError(f"No direction file found for signal={signal} in {direction_dir}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPersistProbDirectionOutputs:
    """Test that persist_probe_direction produces the required output files."""

    def test_gate_json_exists(self, tiny_direction_dir):
        path = tiny_direction_dir / "direction_gate.json"
        assert path.exists(), "direction_gate.json must exist"

    def test_dial_json_exists(self, tiny_direction_dir):
        path = tiny_direction_dir / "direction_dial.json"
        assert path.exists(), "direction_dial.json must exist"

    def test_gate_safetensors_or_npy_exists(self, tiny_direction_dir):
        st = tiny_direction_dir / "direction_gate.safetensors"
        npy = tiny_direction_dir / "direction_gate.npy"
        assert st.exists() or npy.exists(), \
            "direction_gate.safetensors (or fallback .npy) must exist"

    def test_dial_safetensors_or_npy_exists(self, tiny_direction_dir):
        st = tiny_direction_dir / "direction_dial.safetensors"
        npy = tiny_direction_dir / "direction_dial.npy"
        assert st.exists() or npy.exists(), \
            "direction_dial.safetensors (or fallback .npy) must exist"


class TestDirectionUnitNorm:
    """Test (a): direction vectors are unit-norm."""

    def test_gate_direction_unit_norm(self, tiny_direction_dir):
        d = _load_direction_vector(tiny_direction_dir, "gate")
        norm = float(np.linalg.norm(d))
        assert abs(norm - 1.0) < 1e-4, \
            f"Gate direction not unit-norm: norm={norm:.6f}"

    def test_dial_direction_unit_norm(self, tiny_direction_dir):
        d = _load_direction_vector(tiny_direction_dir, "dial")
        norm = float(np.linalg.norm(d))
        assert abs(norm - 1.0) < 1e-4, \
            f"Dial direction not unit-norm: norm={norm:.6f}"

    def test_gate_json_reports_unit_norm(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "gate")
        norm_reported = meta["direction_norm"]
        assert abs(norm_reported - 1.0) < 1e-4, \
            f"direction_gate.json direction_norm={norm_reported:.6f} != 1.0"

    def test_dial_json_reports_unit_norm(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "dial")
        norm_reported = meta["direction_norm"]
        assert abs(norm_reported - 1.0) < 1e-4, \
            f"direction_dial.json direction_norm={norm_reported:.6f} != 1.0"


class TestDirectionMetadata:
    """Test (a): sane layer index + calibration structure."""

    def test_gate_layer_is_valid_int(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "gate")
        layer = meta["best_layer"]
        assert isinstance(layer, int), f"best_layer must be int, got {type(layer)}"
        assert layer >= 0, f"best_layer must be >= 0, got {layer}"

    def test_dial_layer_is_valid_int(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "dial")
        layer = meta["best_layer"]
        assert isinstance(layer, int), f"best_layer must be int, got {type(layer)}"
        assert layer >= 0, f"best_layer must be >= 0, got {layer}"

    def test_gate_auroc_sane(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "gate")
        auroc = meta.get("auroc_at_best_layer")
        assert auroc is not None, "auroc_at_best_layer missing from gate JSON"
        assert 0.5 <= auroc <= 1.0, \
            f"Gate AUROC should be >= 0.5 (better than chance), got {auroc:.4f}"

    def test_dial_auroc_sane(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "dial")
        auroc = meta.get("auroc_at_best_layer")
        assert auroc is not None, "auroc_at_best_layer missing from dial JSON"
        assert 0.5 <= auroc <= 1.0, \
            f"Dial AUROC should be >= 0.5 (better than chance), got {auroc:.4f}"

    def test_gate_calibration_has_required_keys(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "gate")
        cal = meta["calibration"]
        for key in ("positive_mean", "positive_std", "negative_mean", "negative_std",
                    "separation", "n_positive", "n_negative"):
            assert key in cal, f"calibration missing key: {key}"

    def test_dial_calibration_has_required_keys(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "dial")
        cal = meta["calibration"]
        for key in ("positive_mean", "positive_std", "negative_mean", "negative_std",
                    "separation", "n_positive", "n_negative"):
            assert key in cal, f"calibration missing key: {key}"

    def test_gate_calibration_values_in_range(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "gate")
        cal = meta["calibration"]
        assert 0.0 <= cal["positive_mean"] <= 1.0, \
            f"positive_mean out of range: {cal['positive_mean']}"
        assert 0.0 <= cal["negative_mean"] <= 1.0, \
            f"negative_mean out of range: {cal['negative_mean']}"
        assert cal["positive_std"] >= 0.0, \
            f"positive_std must be non-negative: {cal['positive_std']}"

    def test_gate_calibration_positive_gt_negative(self, tiny_direction_dir):
        """With linearly-separable data, positive class should score higher."""
        meta = _load_direction_json(tiny_direction_dir, "gate")
        cal = meta["calibration"]
        assert cal["positive_mean"] > cal["negative_mean"], (
            f"Expected positive_mean > negative_mean for separable data; "
            f"got {cal['positive_mean']:.4f} vs {cal['negative_mean']:.4f}"
        )

    def test_gate_provenance_has_source_dir(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "gate")
        prov = meta["provenance"]
        assert "source_x_dir" in prov, "provenance missing source_x_dir"
        assert "model_tag" in prov, "provenance missing model_tag"

    def test_gate_signal_field(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "gate")
        assert meta["signal"] == "gate"

    def test_dial_signal_field(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "dial")
        assert meta["signal"] == "dial"


class TestDirectionShape:
    """Test that the direction vector shape matches the hidden dim."""

    def test_gate_direction_shape_matches_hidden_dim(self, tiny_direction_dir, synthetic_ext_dir):
        from tests.conftest import HIDDEN_DIM, N_LAYERS
        d = _load_direction_vector(tiny_direction_dir, "gate")
        # The direction dim must match hidden_dim (HIDDEN_DIM in the fixture)
        assert d.shape == (HIDDEN_DIM,), \
            f"Gate direction shape {d.shape} != expected ({HIDDEN_DIM},)"

    def test_dial_direction_shape_matches_hidden_dim(self, tiny_direction_dir, synthetic_ext_dir):
        from tests.conftest import HIDDEN_DIM
        d = _load_direction_vector(tiny_direction_dir, "dial")
        assert d.shape == (HIDDEN_DIM,), \
            f"Dial direction shape {d.shape} != expected ({HIDDEN_DIM},)"


class TestAurocSweepSurface:
    """Test that the AUROC surface is recorded and best layer is the argmax."""

    def test_gate_auroc_surface_best_layer_is_argmax(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "gate")
        surface = meta.get("auroc_surface", {})
        if not surface:
            pytest.skip("auroc_surface not recorded (forced-layer mode)")
        best_reported = meta["best_layer"]
        best_computed = int(max(surface, key=lambda k: surface[k]))
        assert best_reported == best_computed, (
            f"best_layer={best_reported} != argmax of auroc_surface={best_computed}"
        )

    def test_dial_auroc_surface_best_layer_is_argmax(self, tiny_direction_dir):
        meta = _load_direction_json(tiny_direction_dir, "dial")
        surface = meta.get("auroc_surface", {})
        if not surface:
            pytest.skip("auroc_surface not recorded (forced-layer mode)")
        best_reported = meta["best_layer"]
        best_computed = int(max(surface, key=lambda k: surface[k]))
        assert best_reported == best_computed, (
            f"best_layer={best_reported} != argmax of auroc_surface={best_computed}"
        )
