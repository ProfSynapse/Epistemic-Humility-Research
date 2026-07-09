"""Compatibility wrapper for the item-11 experiment-owned Modal launcher."""

from __future__ import annotations

import runpy
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[4]
    / "experiments"
    / "diag-item11-batched-steering-equivalence"
    / "cloud"
    / "modal_item11_equivalence.py"
)

runpy.run_path(str(TARGET), run_name="__main__")
