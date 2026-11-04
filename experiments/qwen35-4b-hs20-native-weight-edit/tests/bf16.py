"""NumPy bfloat16 emulation (round-to-nearest-even) used only to fake engine receipts in tests."""

import numpy as np


def to_bf16(x: np.ndarray) -> np.ndarray:
    a = np.asarray(x, dtype=np.float32)
    bits = a.view(np.uint32).astype(np.uint64)
    rounding = ((bits >> 16) & 1) + 0x7FFF
    out = ((bits + rounding) >> 16) << 16
    return out.astype(np.uint32).view(np.float32)


def realized_delta(w_cols_bf16: np.ndarray, u: np.ndarray, v: np.ndarray, scale: float) -> tuple[float, int]:
    """||bf16(W + s*outer(u,v)) - W||_F over the touched columns, and entries changed (float32 math like the engine)."""
    new = to_bf16(w_cols_bf16.astype(np.float32) + np.float32(scale) * np.outer(u.astype(np.float32), v.astype(np.float32)))
    diff = new.astype(np.float64) - w_cols_bf16.astype(np.float64)
    return float(np.sqrt((diff ** 2).sum())), int((new != w_cols_bf16).sum())
