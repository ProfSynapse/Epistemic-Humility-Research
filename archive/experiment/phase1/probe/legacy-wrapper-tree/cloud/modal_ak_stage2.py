"""Compatibility wrapper for the AK experiment-owned Modal Stage 2 launcher."""

from __future__ import annotations

import runpy
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parents[6]
    / "experiments"
    / "commitment-point"
    / "cloud"
    / "modal_ak_stage2.py"
)

runpy.run_path(str(TARGET), run_name="__main__")
