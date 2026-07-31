#!/usr/bin/env python3
"""Compatibility wrapper for experiments/common/cloud/launch_hf_job.py."""
from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[6]
runpy.run_path(str(ROOT / "experiments/common/cloud/launch_hf_job.py"), run_name="__main__")
