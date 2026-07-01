"""Shared fixtures for Paper 5 / confidence-steering unit tests.

All fixtures are SYNTHETIC (CPU-only, no model downloads, no GPU).
Synthetic extraction dirs replicate the Amendment-Z directory layout:
  - rows.jsonl        (per-row metadata)
  - <key>__pre.safetensors  (pre-anchor hidden states, all layers)
  - <key>__post.safetensors (post-answer hidden states, all layers)
  - manifest.json
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Synthetic extraction dir builder
# ---------------------------------------------------------------------------

N_ROWS = 40           # total rows in the fixture pool
N_LAYERS = 6          # small; real models have 28-40
HIDDEN_DIM = 32       # tiny; real models have 2048-4096
SEED = 42


def _save_shard(path: Path, tensors: dict[str, np.ndarray]) -> None:
    """Save a synthetic shard as safetensors (torch) or numpy fallback."""
    if _TORCH_AVAILABLE:
        try:
            from safetensors.torch import save_file
            import torch as _t
            save_file({k: _t.from_numpy(v.astype(np.float32)) for k, v in tensors.items()},
                      str(path))
            return
        except ImportError:
            pass
    # Fallback: npz (will cause load errors in the actual code — safetensors required)
    np.savez(str(path).replace(".safetensors", ".npz"), **tensors)


def build_synthetic_extraction_dir(
    tmp_path: Path,
    n_correct: int = 10,
    n_wrong: int = 10,
    n_known: int = 10,
    n_halluc: int = 10,
    n_layers: int = N_LAYERS,
    hidden_dim: int = HIDDEN_DIM,
    seed: int = SEED,
    *,
    direction_signal: float = 3.0,
) -> Path:
    """Create a minimal but structurally correct Amendment-X/Z extraction dir.

    The synthetic hidden states are DESIGNED to be linearly separable: each class
    has a Gaussian cluster with mean offset proportional to `direction_signal`
    along dimension 0. This makes the probe fit and direction extraction
    deterministic and verifiable.

    Parameters
    ----------
    tmp_path        : pytest tmp_path (dir is created inside here)
    n_correct, n_wrong, n_known, n_halluc : counts per outcome class
    n_layers        : number of transformer layers to simulate
    hidden_dim      : hidden state dimension
    seed            : RNG seed
    direction_signal: separation of class means in dim-0 (higher = more linearly sep.)
    """
    ext_dir = tmp_path / "synthetic_extraction"
    ext_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(seed)
    outcomes = (
        [("correct", 1)] * n_correct
        + [("wrong", 0)] * n_wrong
        + [("known_answered", 1)] * n_known
        + [("hallucination", 0)] * n_halluc
    )
    random.Random(seed).shuffle(outcomes)

    rows = []
    for i, (outcome, _label) in enumerate(outcomes):
        row_key = f"synthetic__row_{i:04d}"
        is_correct = outcome in ("correct", "known_answered")

        # Build hidden states: class mean separation along dim 0
        mean_val = direction_signal if is_correct else -direction_signal
        base_mean = np.zeros(hidden_dim)
        base_mean[0] = mean_val

        # Pre: answerability signal (known_answered / hallucination drives this)
        pre_is_positive = outcome == "known_answered"
        pre_mean = base_mean.copy()
        pre_mean[0] = direction_signal if pre_is_positive else -direction_signal

        # Post: correctness signal (correct / wrong drives this)
        post_is_positive = outcome == "correct"
        post_mean = base_mean.copy()
        post_mean[0] = direction_signal if post_is_positive else -direction_signal

        # Generate one vector per layer (layers share structure, different noise)
        pre_tensors = {}
        post_tensors = {}
        for li in range(n_layers + 1):  # L0..L<n_layers>
            noise_scale = 0.5 + 0.1 * li
            pre_tensors[f"L{li}"] = (
                pre_mean + rng.normal(0, noise_scale, hidden_dim)
            ).astype(np.float32)
            post_tensors[f"L{li}"] = (
                post_mean + rng.normal(0, noise_scale, hidden_dim)
            ).astype(np.float32)

        safe = row_key.replace("::", "__").replace("|", "_")
        _save_shard(ext_dir / f"{safe}__pre.safetensors", pre_tensors)
        _save_shard(ext_dir / f"{safe}__post.safetensors", post_tensors)

        rows.append({
            "row_key": row_key,
            "dataset": "synthetic",
            "question": f"Synthetic question {i}",
            "source": (
                "answerable" if outcome in ("correct", "wrong")
                else ("selfaware_known" if outcome == "known_answered" else "selfaware_unknown")
            ),
            "answer_text": "Synthetic answer",
            "answered": True,
            "refused": False,
            "correct": (outcome == "correct"),
            "outcome": outcome,
            "prompt_len": 10,
            "answer_tok_len": 5,
            "config_sha": "synthetic_sha_0000",
        })

    rows_path = ext_dir / "rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    manifest = {
        "amendment": "X",
        "base_model": "synthetic/tiny-model",
        "adapter": "NONE",
        "checkpoint": "synthetic",
        "model_tag": "synthetic-tiny",
        "system_prompt": "test",
        "pool_sources": ["synthetic"],
        "enable_thinking": False,
        "n_answerable": n_correct + n_wrong,
        "max_new_tokens": 48,
        "max_attempts": len(rows),
        "seed": seed,
        "persist_dtype": "float32",
        "decode": "greedy",
        "config_sha": "synthetic_sha_0000",
        "n_layers": n_layers,
        "hidden_dim": hidden_dim,
        "n_pool": len(rows),
        "n_attempts": len(rows),
        "n_answered": len(rows),
        "n_correct": n_correct,
        "n_wrong": n_wrong,
        "n_hallucination": n_halluc,
        "n_known_answered": n_known,
        "n_refused": 0,
        "n_empty": 0,
        "out_dir": str(ext_dir),
        "positions": ["pre", "post"],
        "tensor_layer_keys": f"L0..L{n_layers}",
    }
    (ext_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return ext_dir


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def synthetic_ext_dir(tmp_path_factory) -> Path:
    """Synthetic extraction dir (session-scoped for speed)."""
    tmp = tmp_path_factory.mktemp("steering_fixtures")
    return build_synthetic_extraction_dir(tmp)


@pytest.fixture(scope="session")
def tiny_direction_dir(tmp_path_factory, synthetic_ext_dir) -> Path:
    """Run persist_probe_direction on synthetic_ext_dir and return the directions dir.

    This fixture is the integration point: if persist_probe_direction fails, ALL
    downstream tests that depend on this fixture will be marked as errors (not PASS).
    """
    import sys
    import os

    steering_dir = Path(__file__).resolve().parent.parent
    if str(steering_dir) not in sys.path:
        sys.path.insert(0, str(steering_dir))

    from persist_probe_direction import main as ppd_main

    out_dir = tmp_path_factory.mktemp("directions")
    ret = ppd_main([
        "--x-dir", str(synthetic_ext_dir),
        "--out-dir", str(out_dir),
        "--seed", "42",
    ])
    assert ret == 0, "persist_probe_direction failed on synthetic fixture"
    return out_dir
