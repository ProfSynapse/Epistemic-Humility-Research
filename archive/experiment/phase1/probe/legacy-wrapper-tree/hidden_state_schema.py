"""Compatibility wrapper for experiments/common/phase1_probe/hidden_state_schema.py."""

from __future__ import annotations

from _common_phase1_probe_wrapper import reexport_common_phase1_probe_module

_module = reexport_common_phase1_probe_module("hidden_state_schema", globals())
