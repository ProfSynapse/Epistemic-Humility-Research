# j-space-midband-dose-calibration-qwen3-4b

Status: resolved (exploratory FIT-only calibration pass, 2026-07-08).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

This experiment follows directly from the pre-outcome G0 stop in
`j-space-midband-write-sweep-qwen3-4b`. That signed layer-site sweep attempted
to hold the predecessor dose fixed at absolute setpoint 200 across hs23, hs26,
hs29, and hs34. The preparation succeeded and readback was accurate at every
layer, but dose-200 smoke collapsed all dosed hs23 and hs26 rows. The full
held-out contrast was therefore stopped before outcome.

The mechanism lesson is narrow but important: the inherited hs34 dose is not
portable across layer sites. That does not falsify the J-space layer-site
hypothesis; it falsifies the assumption that a single absolute setpoint can be
used before locating each layer's coherent window.

Posture: exploratory dose-calibration cell, local RTX 3090, raw-base
`unsloth/Qwen3-4B` bf16 only. It is not a headline claim and does not touch old
trained-checkpoint cells. It uses FIT rows only; HELD-OUT remains reserved for a
later signed layer contrast using the calibrated setpoints.

## Design

Substrate: raw-base `unsloth/Qwen3-4B`, bf16, no adapter, no 4-bit
quantization.

Inputs:

- Per-layer fitted directions and frozen gates from
  `j-space-midband-write-sweep-qwen3-4b/analysis-committed/`.
- Local gitignored FIT row text from the source experiment's
  `analysis/rows_with_text.jsonl`.
- No held-out rows are used for dose selection.

Layers: hs23, hs26, hs29, hs34.

Dose ladder: absolute setpoints 25, 50, 75, 100, 125, 150, 175, 200.

Calibration subset: 8 FIT confab rows and 8 FIT known-correct rows, stratified
by category where possible, using the source experiment's already-materialized
local rows.

A dose is usable for a layer iff:

- readback is within tolerance for every dosed smoke row,
- collapse on dosed rows is 0,
- FIT confab clean_tighten on the calibration subset is at least 50%.

Selection rule: among usable doses, choose the highest confab clean_tighten
rate, then lower known-correct cost, then lower dose. This produces one frozen
candidate setpoint per layer for a later held-out contrast.

Instrument files pinned at sign: `cell.yaml`, `gates.yaml`,
`calibrate_dose.py`.

## Prediction

Layer-specific calibration will recover non-collapsing usable setpoints for all
four layers, with hs23 and hs26 selecting doses below 200.

## Falsifier

Any layer has no usable dose on the pre-stated ladder, or hs23/hs26 still select
200 or fail to recover from dose-200 collapse, so the immediate J-space
mid-band contrast cannot proceed on this calibration scheme.

## Gates

- **G0 (input validity; stop, not outcome)**: source committed directions,
  build manifest, gate fit, and smoke summary are present; local row text exists
  only under the source experiment's gitignored `analysis/`; calibration rows
  are all FIT rows.
- **G1 (usable setpoint per layer)**: hs23, hs26, hs29, and hs34 each have at
  least one usable dose by the rule above.
- **G2 (collapse recovery where needed)**: hs23 and hs26 recover from the
  dose-200 collapse by selecting usable doses below 200.
- **G3 (actionable output)**: the output summary reports selected doses for all
  four layers.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Calibration will recover hs23/hs26 at lower doses, likely around 75-150; hs29/hs34 should remain usable near 175-200. |
| user | |

## Outcome

Resolved 2026-07-08 as an exploratory FIT-only calibration pass.

Summary: layer-specific calibration recovered non-collapsing usable setpoints
for all four layers, and the two layers that collapsed at dose 200 recovered at
lower doses. Selected absolute setpoints are hs23=25, hs26=75, hs29=125, and
hs34=175.

Committed artifact:

- `analysis-committed/dose_calibration_summary.json`

Gate results:

- **G0 input validity**: passed. The run used committed directions/build/gate
  artifacts from `j-space-midband-write-sweep-qwen3-4b`; row text remained local
  under gitignored `analysis/`; calibration rows were FIT rows only.
- **G1 usable setpoint per layer**: passed. All four layers have at least one
  usable dose by the pre-stated rule.
- **G2 collapse recovery where needed**: passed. hs23 selected 25 and hs26
  selected 75; both are below 200 and have zero collapse on dosed rows. At dose
  200, hs23 and hs26 both still had collapse_rate_on_dosed=1.0, confirming that
  the lower-dose recovery, not a changed classifier, is what cleared the gate.
- **G3 actionable output**: passed. The summary reports selected doses for all
  four layers.

Selected-dose table on the 8 FIT confab + 8 FIT known-correct calibration rows:

| Layer | Selected dose | Readback mean | Collapse on dosed | Confab clean_tighten | Known-correct cost |
|-------|---------------|---------------|-------------------|----------------------|--------------------|
| hs23 | 25 | 25.0055 | 0/9 | 8/8 | 1/8 |
| hs26 | 75 | 74.9836 | 0/9 | 8/8 | 1/8 |
| hs29 | 125 | 125.0173 | 0/9 | 8/8 | 1/8 |
| hs34 | 175 | 175.0389 | 0/9 | 7/8 | 1/8 |

Interpretation: the G0 stop in the predecessor sweep was a dose-portability
failure, not evidence that hs23/hs26 are unusable write sites. Lower setpoints
restore coherent behavior at the mid-band sites on FIT rows. This does not test
held-out layer superiority; the next evidence-producing step is a fresh signed
held-out hs23/hs26/hs29 vs hs34 contrast using the calibrated setpoints.
