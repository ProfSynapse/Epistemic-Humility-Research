#!/usr/bin/env python3
"""Compatibility wrapper for experiments/common/phase1_probe/probe.py."""

from __future__ import annotations

from _common_phase1_probe_wrapper import reexport_common_phase1_probe_module

_module = reexport_common_phase1_probe_module("probe", globals())

if __name__ == "__main__":
    raise SystemExit(_module.main())
