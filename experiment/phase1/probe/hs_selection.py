"""Compatibility wrapper for experiments/common/phase1_probe/hs_selection.py."""

from __future__ import annotations

from _common_phase1_probe_wrapper import reexport_common_phase1_probe_module

_module = reexport_common_phase1_probe_module("hs_selection", globals())
