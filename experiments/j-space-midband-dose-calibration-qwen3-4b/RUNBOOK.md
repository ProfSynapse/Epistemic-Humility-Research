---
title: 'J-space mid-band dose calibration on Qwen3-4B'
kg:
  id: experiment:j-space-midband-dose-calibration-qwen3-4b
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: done
governance: exploratory
track: mechanism
lane: local
est_compute: 'Completed locally on RTX 3090; FIT-only 4-layer x 8-dose calibration over 16 rows.'
relationships:
  - type: tests
    target: '[[j-space-mediated-actuation-fragility]]'
    target_id: mechanism:j-space-mediated-actuation-fragility
    confidence: medium
  - type: builds_on
    target: '[[j-space-localization-qwen3-4b]]'
    target_id: experiment:j-space-localization-qwen3-4b
    confidence: high
  - type: related_to
    target: '[[activation-addition]]'
    target_id: method:activation-addition
    confidence: medium
  - type: related_to
    target: '[[steering-vector]]'
    target_id: term:steering-vector
    confidence: medium
related:
  - '[[j-space-mediated-actuation-fragility]]'
  - '[[j-space-localization-qwen3-4b]]'
  - '[[activation-addition]]'
  - '[[steering-vector]]'
---

## Question & Hypothesis

Can layer-specific dose calibration recover non-collapsing usable erase-write
setpoints for hs23, hs26, hs29, and hs34 after absolute dose 200 collapsed hs23
and hs26 in the predecessor J-space mid-band write sweep smoke?

Prediction: all four layers recover usable setpoints, with hs23 and hs26
selecting below 200.

Falsifier: any layer has no usable dose on the pre-stated ladder, or hs23/hs26
still select 200 or fail to recover from dose-200 collapse.

## Design

The governed source of truth is
`experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md`. The run
uses raw-base `unsloth/Qwen3-4B` bf16, no adapter, and the per-layer directions
and gates committed by `j-space-midband-write-sweep-qwen3-4b`.

The calibration surface is FIT-only: 8 confab rows and 8 known-correct rows
from the source experiment. Held-out rows remain untouched for a later signed
layer-site contrast.

## Prerequisites & Gating

The source experiment's committed build manifest, gate fit, smoke summary, and
per-layer directions had to be present. FIT row text had to exist locally under
the source experiment's gitignored `analysis/` directory and must not be
committed.

The run was gated by the signed amendment and explicit local GPU approval. The
pre-stated usable-dose rule required readback within tolerance, zero collapse on
dosed rows, and FIT confab clean_tighten at least 50%.

## Runbook

1. Read `experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md`.
2. Launch locally from the experiment directory with:
   `PYTHONPATH=/home/profsynapse/code/ehr-worktrees/j-space/synaptic-tuner python calibrate_dose.py --n-confab 8 --n-known 8 --doses 25 50 75 100 125 150 175 200`.
3. Confirm `analysis-committed/dose_calibration_summary.json` is aggregate-only
   before staging it.
4. Resolve with the `bin/exp` wrapper's `resolve` command and regenerate the
   experiment registry.

## Result

Resolved 2026-07-08 as an exploratory FIT-only calibration pass. All layers had
usable non-collapsing setpoints, and the two layers that collapsed at dose 200
recovered below 200:

- hs23 selected 25
- hs26 selected 75
- hs29 selected 125
- hs34 selected 175

At the selected doses, readback was within tolerance, collapse on dosed rows was
0, FIT confab clean_tighten was 8/8 for hs23/hs26/hs29 and 7/8 for hs34, and
known-correct cost was 1/8 for every layer.

The committed public summary is
`experiments/j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json`.

## Validation contract

Definition of done: the committed summary reports selected doses for all four
layers, `all_layers_have_usable_dose=true`, `collapsed_at_200_recovered=true`,
the amendment Outcome records the gate calls, row text remains gitignored, and
`bin/exp validate` passes.

## Outputs & provenance

Committed outputs live under
`experiments/j-space-midband-dose-calibration-qwen3-4b/analysis-committed/`.
The run command and log remain under the local gitignored `analysis/` directory.
The public summary contains aggregate counts, rates, readback means, and
selected doses only.

## Interpretation

This supports the narrow lesson that the predecessor G0 stop was a
dose-portability failure rather than evidence that hs23 or hs26 cannot be write
sites. It does not yet establish held-out mid-band superiority. The next
evidence-producing step is a fresh signed held-out hs23/hs26/hs29 versus hs34
contrast using these calibrated setpoints.

## Variations

- Predecessor dose-200 smoke: stopped at G0 because hs23/hs26 collapsed.
- FIT-only dose calibration `jspace-midband-dose-calibration-r1`: completed and
  resolved.
- Proposed next variant: calibrated held-out layer-site contrast using
  hs23=25, hs26=75, hs29=125, hs34=175.

## Status log

- 2026-07-08: Local RTX 3090 run completed and experiment resolved.
