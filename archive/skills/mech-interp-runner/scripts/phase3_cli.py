#!/usr/bin/env python3
"""Archived compatibility wrapper for the retired phase3_cli.py entrypoint.

Active agents should use:

    python .skills/mech-interp-runner/scripts/mechinterp_cli.py

This archived copy records the July 2026 rename away from phase-numbered
workflow naming.
"""
from __future__ import annotations

from mechinterp_cli import main


if __name__ == "__main__":
    raise SystemExit(main())
