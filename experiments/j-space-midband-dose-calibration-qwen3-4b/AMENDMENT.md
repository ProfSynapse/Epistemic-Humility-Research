# j-space-midband-dose-calibration-qwen3-4b

Status: signed (not launched; local dose calibration still requires launch approval).

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

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
