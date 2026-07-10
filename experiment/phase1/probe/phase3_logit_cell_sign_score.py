#!/usr/bin/env python3
"""Compatibility wrapper for the shared logit-cell sign scorer."""
from __future__ import annotations

from _common_mechinterp_wrapper import reexport_common_mechinterp_module

_module = reexport_common_mechinterp_module("logit_cell_sign_score", globals())

if __name__ == "__main__":
    raise SystemExit(_module.main())
