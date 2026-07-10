#!/usr/bin/env python3
"""Compatibility wrapper for the shared gold behavior panel helper."""
from __future__ import annotations

from _common_mechinterp_wrapper import reexport_common_mechinterp_module

_module = reexport_common_mechinterp_module("gold_behavior_panel", globals())

if __name__ == "__main__":
    raise SystemExit(_module.main())
