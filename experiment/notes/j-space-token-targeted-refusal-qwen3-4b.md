---
title: 'J-space token-targeted refusal write on Qwen3-4B'
kg:
  id: experiment:j-space-token-targeted-refusal-qwen3-4b
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: done
governance: exploratory
phase: phase1
lane: local
est_compute: 'Completed locally on RTX 3090; 443-row held-out steer cell after FIT-only dose selection.'
relationships:
  - type: tests
    target: '[[j-space-mediated-actuation-fragility]]'
    target_id: mechanism:j-space-mediated-actuation-fragility
    confidence: medium
  - type: builds_on
    target: '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
    target_id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
    confidence: high
  - type: related_to
    target: '[[jacobian-lens]]'
    target_id: method:jacobian-lens
    confidence: high
  - type: related_to
    target: '[[activation-addition]]'
    target_id: method:activation-addition
    confidence: medium
related:
  - '[[j-space-mediated-actuation-fragility]]'
  - '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
  - '[[jacobian-lens]]'
  - '[[activation-addition]]'
---

## Question & Hypothesis

Can an internal J-lens token-target refusal write at hs23 improve the resolved
doubt-gated `c_hat` caution snap on raw-base Qwen3-4B bf16 without increasing
known-correct cost?

Prediction: the hs23 hybrid of `c_hat` plus a refusal-token direction improves
held-out confab clean_tighten over `c_hat_only` by at least 4 percentage points,
keeps known-correct cost within +2 percentage points, and beats a matched random
J-space control by at least 3 percentage points.

## Design

The governed source of truth is
`experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md`. The run uses
raw-base `unsloth/Qwen3-4B` bf16, no adapter, and the same doubt gate and
workspace-band `c_hat` actuator lineage as the calibrated J-space layer contrast.

The token-target direction was fit from FIT-only prompt gradients that raise a
fixed natural refusal/absence token bundle and lower answer/reply continuation
tokens. Held-out rows were untouched until after the instrument was signed.

## Prerequisites & Gating

The predecessor J-space localization, calibrated layer contrast, gate-fit, and
dose-calibration committed artifacts must exist. Local row text must remain only
under gitignored `analysis/` directories. The token bundle must be audited before
direction fitting, the instrument must be signed with `bin/exp sign`, and any GPU
run requires the explicit local GPU acknowledgement flag used by the runner.

## Runbook

1. Read `experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md`.
2. Audit the token bundle with
   `experiments/j-space-token-targeted-refusal-qwen3-4b/token_bundle_audit.py`.
3. Build FIT-only token directions with
   `experiments/j-space-token-targeted-refusal-qwen3-4b/run_token_target.py`.
4. Run smoke, FIT calibration, then the held-out full run through the same
   runner after signing the instrument.
5. Confirm committed outputs under
   `experiments/j-space-token-targeted-refusal-qwen3-4b/analysis-committed/`
   are aggregate-only or direction artifacts.
6. Resolve with `bin/exp`, regenerate the experiments registry, and
   update this note plus the J-space mechanism note.

## Result

Resolved 2026-07-08 as an exploratory falsification. The token-target write was
controllable and safe, but did not add meaningful lift over `c_hat_only`:

- hs23 `c_hat_only`: 165/185 = 89.2% confab clean_tighten; 9/258 = 3.5%
  known-correct cost.
- hs23 `c_hat_plus_j_token`: 166/185 = 89.7% confab clean_tighten; 10/258 =
  3.9% known-correct cost.
- hs23 `c_hat_plus_random_j`: 165/185 = 89.2% confab clean_tighten.
- hs23 `j_token_only`: 88/185 = 47.6% confab clean_tighten.

G1 and G3 failed; G2 and G4 passed. All write readbacks were 100% within
tolerance, and the run committed only aggregate summaries plus fitted direction
artifacts.

## Interpretation

The natural token-target direction is not inert: by itself it moves nearly half
of held-out confab rows into clean refusals. But once the stronger workspace-band
`c_hat` snap is active, the natural token-target addition is mostly redundant.
This constrains the J-space actuation bridge: a verbalizable token direction can
be a real write direction without being an additive optimizer for the regulated
refusal controller.

## Validation contract

Definition of done: `analysis-committed/full_summary.json` exists; `AMENDMENT.md`
records G0-G4; `experiment.yaml` is terminal; `bin/exp validate` and
`bin/exp regen --check` pass; KG relationship validation has no new errors; and
private row checkpoints are excluded from git.

## Outputs & provenance

Committed aggregate outputs live under
`experiments/j-space-token-targeted-refusal-qwen3-4b/analysis-committed/`.
Private row-level checkpoints remain under the experiment's gitignored
`analysis/` directory and are not source of public claims.

## Variations

- Natural observed token bundle: completed and falsified as the first option-2
  actuator.
- Dense English or multilingual token-packing variants: deferred to a separate
  screen so this result's token bundle is not moved post hoc.
- Generic compound-write tuner support: infrastructure follow-up, not evidence
  for this result.

## Status log

- 2026-07-08: Local RTX 3090 held-out run completed and experiment resolved as
  falsified.
