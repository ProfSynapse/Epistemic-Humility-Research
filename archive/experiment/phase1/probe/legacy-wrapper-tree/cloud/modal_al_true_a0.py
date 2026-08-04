"""Compatibility wrapper for the AL experiment-owned Modal launcher."""

from __future__ import annotations

import runpy
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[6]
    / "experiments"
    / "radial-anti-propensity-steering"
    / "cloud"
    / "modal_al_true_a0.py"
)

runpy.run_path(str(TARGET), run_name="__main__")
