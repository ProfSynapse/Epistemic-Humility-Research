#!/usr/bin/env python3
"""Compatibility wrapper for the shared residual caution direction fitter."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[5]
TARGET_DIR = ROOT / "experiments/common/mechinterp"
TARGET = TARGET_DIR / "residual_caution_direction.py"

if str(TARGET_DIR) not in sys.path:
    sys.path.insert(0, str(TARGET_DIR))

_spec = importlib.util.spec_from_file_location("_residual_caution_direction_impl", TARGET)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load {TARGET}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

for _name in dir(_module):
    if _name not in {"__builtins__", "__cached__", "__file__", "__loader__", "__name__", "__package__", "__spec__"}:
        globals()[_name] = getattr(_module, _name)

if __name__ == "__main__":
    raise SystemExit(_module.main())
