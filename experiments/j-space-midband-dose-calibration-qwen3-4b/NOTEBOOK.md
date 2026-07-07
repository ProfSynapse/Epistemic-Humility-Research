# j-space-midband-dose-calibration-qwen3-4b notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-07 - signed

Signed the FIT-only dose-calibration instrument. Pinned files:
`cell.yaml`, `gates.yaml`, and `calibrate_dose.py`. No calibration GPU run has
been launched yet.

### 2026-07-07 - scaffolded

Created as the governed follow-up to the G0 stop in
`j-space-midband-write-sweep-qwen3-4b`. It calibrates layer-specific dose
windows on FIT rows only and does not touch held-out rows. The intended output
is a selected non-collapsing setpoint per layer, suitable for a later signed
held-out layer contrast.
