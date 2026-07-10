"""Compatibility wrapper for the AM experiment-owned Modal launcher."""

from __future__ import annotations

import runpy
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[4]
    / "experiments"
    / "residual-catch-veto-coverage"
    / "cloud"
    / "modal_am_residual_catch.py"
)

runpy.run_path(str(TARGET), run_name="__main__")
