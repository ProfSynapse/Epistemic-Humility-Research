#!/usr/bin/env python3
"""Compatibility wrapper for the dark-actuator-screen census script."""
from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(
    str(ROOT / "experiments/dark-actuator-screen/dark_displacement_census.py"),
    run_name="__main__",
)
