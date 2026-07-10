#!/usr/bin/env python3
"""Compatibility wrapper for the item 20 experiment-owned diagnostic script."""
from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(
    str(ROOT / "experiments/diag-item20-gentime-displacement/diag_item20_gentime_decomposition.py"),
    run_name="__main__",
)
