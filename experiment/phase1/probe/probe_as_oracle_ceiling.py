#!/usr/bin/env python3
"""Compatibility wrapper for the probe-as-oracle readout-ceiling scorer."""
from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(
    str(ROOT / "experiments/probe-as-oracle-readout-ceiling/probe_as_oracle_ceiling.py"),
    run_name="__main__",
)
