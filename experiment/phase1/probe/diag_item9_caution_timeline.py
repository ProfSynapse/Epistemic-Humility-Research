#!/usr/bin/env python3
"""Compatibility wrapper for the item 9 experiment-owned diagnostic script."""
from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(
    str(ROOT / "experiments/diag-item9-caution-assembly-timeline/diag_item9_caution_timeline.py"),
    run_name="__main__",
)
