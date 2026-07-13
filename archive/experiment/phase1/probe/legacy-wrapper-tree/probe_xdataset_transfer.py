#!/usr/bin/env python3
"""Compatibility wrapper for the xdataset-probe-transfer scorer."""
from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(
    str(ROOT / "experiments/xdataset-probe-transfer/probe_xdataset_transfer.py"),
    run_name="__main__",
)
