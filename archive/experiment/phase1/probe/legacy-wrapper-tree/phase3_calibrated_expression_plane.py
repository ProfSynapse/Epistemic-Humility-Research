#!/usr/bin/env python3
"""Compatibility wrapper for the shared calibrated-expression plane helper."""
from __future__ import annotations

from _common_mechinterp_wrapper import reexport_common_mechinterp_module

_module = reexport_common_mechinterp_module("calibrated_expression_plane", globals())

if __name__ == "__main__":
    raise SystemExit(_module.main())
