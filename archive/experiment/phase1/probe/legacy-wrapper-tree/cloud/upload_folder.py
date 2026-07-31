#!/usr/bin/env python3
"""Compatibility wrapper for experiments/common/cloud/upload_folder.py."""
from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[6]
runpy.run_path(str(ROOT / "experiments/common/cloud/upload_folder.py"), run_name="__main__")
