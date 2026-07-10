#!/usr/bin/env python3
"""Compatibility wrapper for the shared behavior-axis scan helper."""
from __future__ import annotations

from _common_mechinterp_wrapper import reexport_common_mechinterp_module

_module = reexport_common_mechinterp_module("behavior_axis_scan", globals())

if __name__ == "__main__":
    raise SystemExit(_module.main())
