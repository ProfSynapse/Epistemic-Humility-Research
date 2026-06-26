#!/usr/bin/env python3
"""Config loading + extraction-id helpers for the hidden-state harness.

Split out of hidden_state_probe.py (SRP refactor). Holds the PROBE_DIR-free
config primitives. The PROBE_DIR-anchored resolvers (resolve_eval_arm_adapters,
resolve_output_dir, parse_config) stay in the hidden_state_probe facade because
they read PROBE_DIR, which is the test monkeypatch seam (see hs_paths).
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def extraction_id(arm_name: str, extraction_config_sha: str) -> str:
    """Per-arm output id: f'{arm}__{extraction_config_sha[:12]}' (Decision C)."""
    return f"{arm_name}__{extraction_config_sha[:12]}"
