"""Anchor-tensor loading for evidence-response-direction-search (M4c). Pure
CPU. Loads `anchor__L20` vectors for specific row_keys from the reused M4-WK
channel-1 capture arms, keyed by the row_key -> file mapping in each arm's
`capture/capture.jsonl` (never assumes on-disk file order == row_key order).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from safetensors import safe_open

import common
import config


def build_id_to_file_map(arm: str) -> dict[str, str]:
    capture_jsonl = config.CAPTURE_SOURCE_DIR / arm / "capture" / "capture.jsonl"
    rows = common.load_jsonl(capture_jsonl)
    return {r["id"]: r["file"] for r in rows}


def build_id_to_role_map(arm: str) -> dict[str, str]:
    capture_jsonl = config.CAPTURE_SOURCE_DIR / arm / "capture" / "capture.jsonl"
    rows = common.load_jsonl(capture_jsonl)
    return {r["id"]: r["role"] for r in rows}


def load_anchor(arm: str, row_key: str, id_to_file: dict[str, str] | None = None) -> np.ndarray:
    if id_to_file is None:
        id_to_file = build_id_to_file_map(arm)
    if row_key not in id_to_file:
        raise KeyError(f"row_key {row_key!r} not found in arm {arm!r} capture.jsonl")
    tensor_path = config.CAPTURE_SOURCE_DIR / arm / "capture" / id_to_file[row_key]
    with safe_open(str(tensor_path), framework="numpy") as f:
        vec = f.get_tensor(config.ANCHOR_TENSOR_KEY)
    return np.asarray(vec, dtype=np.float64)


def load_anchors(arm: str, row_keys: list[str]) -> np.ndarray:
    """Returns an (n, hidden_dim) float64 matrix, rows in the SAME order as
    `row_keys` (caller-controlled order, not file order)."""
    id_to_file = build_id_to_file_map(arm)
    return np.stack([load_anchor(arm, rk, id_to_file) for rk in row_keys])
