# Shared Readout Implementations

This directory holds reusable two-signal readout implementation code promoted
from the legacy Amendment S/T/U/V/W/X scripts.

The thin modules still present under `archive/experiment/phase1/probe/amendment_*.py`
are compatibility wrappers for pinned historical instruments and older runner
commands. New code should import the implementation from
`experiments.common.readouts`.

These modules still read and write the same legacy artifact directories by
default when run through the wrappers; only the source-code home changed.
