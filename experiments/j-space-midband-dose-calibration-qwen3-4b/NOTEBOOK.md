# j-space-midband-dose-calibration-qwen3-4b notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-08 - resolved

Local run completed at 2026-07-08T10:36:46Z and wrote
`analysis-committed/dose_calibration_summary.json`. All gates passed:
G1 all layers had usable setpoints, G2 hs23/hs26 recovered below dose 200, and
G3 selected doses were reported for all layers.

Selected absolute setpoints: hs23=25, hs26=75, hs29=125, hs34=175. This remains
FIT-only calibration evidence; held-out layer-site behavior is reserved for a
new signed contrast.

### 2026-07-08 - local launch

User approved launching `j-space-midband-dose-calibration-qwen3-4b` on the local
RTX 3090. Status moved to `running` before launch. Command:
`PYTHONPATH=/home/profsynapse/code/ehr-worktrees/j-space/synaptic-tuner python
calibrate_dose.py --n-confab 8 --n-known 8 --doses 25 50 75 100 125 150 175
200`.

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
