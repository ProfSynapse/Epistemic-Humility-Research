#!/usr/bin/env python3
"""Compatibility wrapper for the shared residual read-trajectory analyzer."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[3]
TARGET_DIR = ROOT / "experiments/common/mechinterp"
TARGET = TARGET_DIR / "residual_read_trajectory.py"

if str(TARGET_DIR) not in sys.path:
    sys.path.insert(0, str(TARGET_DIR))

if "residual_read_trajectory" in sys.modules:
    _module = sys.modules["residual_read_trajectory"]
else:
    _spec = importlib.util.spec_from_file_location("residual_read_trajectory", TARGET)
    if _spec is None or _spec.loader is None:
        raise ImportError(f"cannot load {TARGET}")
    _module = importlib.util.module_from_spec(_spec)
    sys.modules["residual_read_trajectory"] = _module
    _spec.loader.exec_module(_module)

for _name in dir(_module):
    if _name not in {"__builtins__", "__cached__", "__file__", "__loader__", "__name__", "__package__", "__spec__"}:
        globals()[_name] = getattr(_module, _name)

if __name__ == "__main__":
    raise SystemExit(_module.main())
