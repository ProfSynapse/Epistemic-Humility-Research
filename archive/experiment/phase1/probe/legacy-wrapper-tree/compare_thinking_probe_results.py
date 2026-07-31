#!/usr/bin/env python3
"""Compatibility wrapper for the thinking-enabled parallel arm comparator."""
from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[5]
runpy.run_path(
    str(ROOT / "experiments/thinking-enabled-parallel-arm/compare_thinking_probe_results.py"),
    run_name="__main__",
)
