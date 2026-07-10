#!/usr/bin/env python3
"""Compatibility wrapper for experiments/common/mechinterp/head_localization_scan.py."""

from __future__ import annotations

from _common_mechinterp_wrapper import reexport_common_mechinterp_module

_module = reexport_common_mechinterp_module("head_localization_scan", globals())

if __name__ == "__main__":
    raise SystemExit(_module.main())
