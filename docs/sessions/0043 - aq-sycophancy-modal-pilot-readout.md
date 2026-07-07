---
schema_version: research-session/v1
session_id: '0043'
title: AQ sycophancy Modal pilot readout
status: active
created_at: '2026-07-07T17:20:14Z'
updated_at: '2026-07-07T17:20:14Z'
phase: phase1
question: Can the AQ answer-sycophancy pilot produce a separable activation readout on official Qwen3-4B, and is the row pool sufficient to license steering?
tags:
- aq
- sycophancy
- modal
- mechinterp
run_ids:
- ap-JqoCvvgwbGHSKqkCux9CcM
- fc-01KWYMPM3A5P5QFPZD29AGXS9M
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: AQ is an exploratory sycophancy read-vs-write cell, separate from the locked Phase 1 headline matrix.
  changed_by_session: Readout signal found on the pilot pool, but AQ-G0 row-count gate failed; actuator launch is not licensed from this pool.
checkpoints:
- id: 001-launch
  at: '2026-07-07T17:20:14Z'
  kind: launch
  title: Modal smoke and readout launched
  summary: User authorized the AQ Modal smoke/readout path on official base Qwen3-4B, not a Synaptic-trained variant; the final readout run used repo commit d5f26f4cb on Modal A10G.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py
  - experiments/aq-sycophancy-activation-actuator/AMENDMENT.md
  run_ids:
  - ap-JqoCvvgwbGHSKqkCux9CcM
  commands:
  - modal run --detach experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py --readout --repo-commit=d5f26f4cb
  decisions:
  - Use official Qwen/Qwen3-4B at revision 1cfa9a7208912126459214e8b04321603b3df60c.
  next_steps: []
  signals: {}
- id: 002-result
  at: '2026-07-07T17:20:14Z'
  kind: result
  title: Readout completed with separable pilot direction
  summary: Extraction captured 32/32 answered rows; probe-fit selected a normalized layer-20 direction with AUROC 1.00 on 9 positive and 7 negative pilot labels. Other AUROCs were L12=0.70, L16=0.80, L17=0.90, and L24=0.90.
  evidence:
  - professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/experiments/aq-sycophancy-activation-actuator/directions/sycophancy_answer_direction.json
  - professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/experiments/aq-sycophancy-activation-actuator/analysis/extraction/manifest.json
  run_ids:
  - fc-01KWYMPM3A5P5QFPZD29AGXS9M
  commands: []
  decisions: []
  next_steps: []
  signals:
    selected_layer: 20
    auroc: 1.0
    n_positive: 9
    n_negative: 7
- id: 003-interpretation
  at: '2026-07-07T17:20:14Z'
  kind: interpretation
  title: AQ-G0 failed; no actuator verdict
  summary: The pilot supports the user's expectation that an answer-sycophancy readout exists, but AQ-G0 requires at least 20 positive and 20 negative incorrect-hint labels and this run produced only 9/7. Therefore the registered gate is underpowered/void and the actuator stage should wait for a scaled or revised row-pool plan.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/gates.yaml
  - experiments/aq-sycophancy-activation-actuator/row_pool.yaml
  - experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md
  run_ids: []
  commands: []
  decisions:
  - Do not treat the layer-20 AUROC as AQ-G1 pass under the registered gate because AQ-G0 did not pass.
  next_steps:
  - Scale or revise the row-pool construction to satisfy AQ-G0 before any actuator launch.
  - Re-run readout on the scaled pool and then ask for explicit actuator launch approval.
  signals: {}
- id: 004-decision
  at: '2026-07-07T17:20:14Z'
  kind: decision
  title: Scale next AQ pass to 512 source rows
  summary: User requested a larger dataset, closer to 500 rows. The next AQ eval config was updated from limit 64 to limit 512, with Modal staging tags moved to r2 to keep scaled artifacts separate from the r1 pilot.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/eval_16bit_sycophancy_answer.yaml
  - experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py
  - experiments/aq-sycophancy-activation-actuator/row_pool.yaml
  run_ids: []
  commands: []
  decisions:
  - Use `limit: 512` for the next AQ row-pool smoke/readout pass.
  - Keep actuator launch blocked until r2 scored rows clear AQ-G0.
  next_steps:
  - Validate and dry-run the r2 wrapper.
  - After user approval, launch r2 smoke/readout on Modal.
  signals: {}
---
# AQ sycophancy Modal pilot readout

## Question

Can the AQ answer-sycophancy pilot produce a separable activation readout on
official Qwen3-4B, and is the row pool sufficient to license steering?

## Trajectory Position

AQ is a tier-2 exploratory sycophancy read-vs-write cell, separate from the
locked Phase 1 headline matrix. This session records a pilot/smoke readout, not
a resolved amendment verdict.

## Summary

The Modal run completed and found a strong activation readout on the pilot pool:
layer 20 AUROC 1.00 over 9 positive and 7 negative labels, with 32/32 rows
captured. The registered AQ gate does not pass because AQ-G0 requires at least
20 positive and 20 negative incorrect-hint rows. The honest state is "readout
signal found; row pool underpowered; actuator not licensed yet."

## Checkpoints

### 001-launch - Modal smoke and readout launched

- at: `2026-07-07T17:20:14Z`
- kind: `launch`
- summary: User authorized the AQ Modal smoke/readout path on official base Qwen3-4B, not a Synaptic-trained variant; the final readout run used repo commit d5f26f4cb on Modal A10G.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py`
  - `experiments/aq-sycophancy-activation-actuator/AMENDMENT.md`
- run ids:
  - `ap-JqoCvvgwbGHSKqkCux9CcM`
- commands:
  - `modal run --detach experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py --readout --repo-commit=d5f26f4cb`
- decisions:
  - Use official `Qwen/Qwen3-4B` at revision `1cfa9a7208912126459214e8b04321603b3df60c`.

### 002-result - Readout completed with separable pilot direction

- at: `2026-07-07T17:20:14Z`
- kind: `result`
- summary: Extraction captured 32/32 answered rows; probe-fit selected a normalized layer-20 direction with AUROC 1.00 on 9 positive and 7 negative pilot labels. Other AUROCs were L12=0.70, L16=0.80, L17=0.90, and L24=0.90.
- evidence:
  - `professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/experiments/aq-sycophancy-activation-actuator/directions/sycophancy_answer_direction.json`
  - `professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/experiments/aq-sycophancy-activation-actuator/analysis/extraction/manifest.json`
- run ids:
  - `fc-01KWYMPM3A5P5QFPZD29AGXS9M`

### 003-interpretation - AQ-G0 failed; no actuator verdict

- at: `2026-07-07T17:20:14Z`
- kind: `interpretation`
- summary: The pilot supports the user's expectation that an answer-sycophancy readout exists, but AQ-G0 requires at least 20 positive and 20 negative incorrect-hint labels and this run produced only 9/7. Therefore the registered gate is underpowered/void and the actuator stage should wait for a scaled or revised row-pool plan.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/gates.yaml`
  - `experiments/aq-sycophancy-activation-actuator/row_pool.yaml`
  - `experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md`
- decisions:
  - Do not treat the layer-20 AUROC as AQ-G1 pass under the registered gate because AQ-G0 did not pass.
- next steps:
  - Scale or revise the row-pool construction to satisfy AQ-G0 before any actuator launch.
  - Re-run readout on the scaled pool and then ask for explicit actuator launch approval.

### 004-decision - Scale next AQ pass to 512 source rows

- at: `2026-07-07T17:20:14Z`
- kind: `decision`
- summary: User requested a larger dataset, closer to 500 rows. The next AQ eval config was updated from `limit: 64` to `limit: 512`, with Modal staging tags moved to r2 to keep scaled artifacts separate from the r1 pilot.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/eval_16bit_sycophancy_answer.yaml`
  - `experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py`
  - `experiments/aq-sycophancy-activation-actuator/row_pool.yaml`
- decisions:
  - Use `limit: 512` for the next AQ row-pool smoke/readout pass.
  - Keep actuator launch blocked until r2 scored rows clear AQ-G0.
- next steps:
  - Validate and dry-run the r2 wrapper.
  - After user approval, launch r2 smoke/readout on Modal.
