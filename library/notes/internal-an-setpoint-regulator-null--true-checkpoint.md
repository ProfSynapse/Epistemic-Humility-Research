---
title: 'Propensity-Selected Caution Setpoint Write Did Not Regulate Confabulation, but the Null Is Confounded by an Unvalidated Actuator (Amendment AN, TRUE checkpoint)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-an-setpoint-regulator-null
  type: paper
  status: canonical
year: 2026
area: epistemic-humility
status: lab-notebook
source: internal
source_kind: epistemic-humility-research-program
authors:
- Joseph Rosenbaum (Synaptic Labs)
models:
- qwen3-4b
metrics:
- auroc
fulltext: ../../experiment/protocol/AMENDMENT-AN-selected-setpoint-regulator.md
provenance: 'Internal exploratory result (Tier-2, signed pre-registered amendment, not a paper draft). Source of truth: experiment/protocol/AMENDMENT-AN-selected-setpoint-regulator.md (signed 2026-07-05, resolved 2026-07-06) plus analysis/amendment_an_prep/amendment_an_run/ (gates_report.json, smoke_primary/readback.json). Surface: AL frozen AI-TRUE A0 baseline (1662 rows: 116 confab / 90 correct / 120 wrong / 114 answerable-refused / 1222 unanswerable-refused), regenerated under three arms (primary propensity-flagged, permuted-flag control, descriptive dose ladder) on the same checkpoint, system prompt, greedy decoding, and grader as the AL A0 cell. Single seed, local RTX 3090, no cloud spend. Scripts committed on branch amendment-an-selected-setpoint-regulator.'
related:
- '[[setpoint-write-on-caution-perp-does-not-actuate-fabrication]]'
- '[[confabulation-propensity-direction]]'
- '[[confab-cloud]]'
- '[[confab-propensity-push-reaches-confab-cloud]]'
- '[[high-probe-accuracy-does-not-imply-causal-use]]'
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
- '[[activation-steering]]'
- '[[causal-intervention]]'
- '[[auroc]]'
relationships:
- type: supports
  target: '[[setpoint-write-on-caution-perp-does-not-actuate-fabrication]]'
  target_id: mechanism:setpoint-write-on-caution-perp-does-not-actuate-fabrication
  confidence: high
- type: studies
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: studies
  target: '[[confab-cloud]]'
  target_id: term:confab-cloud
  confidence: high
- type: related_to
  target: '[[confab-propensity-push-reaches-confab-cloud]]'
  target_id: mechanism:confab-propensity-push-reaches-confab-cloud
  confidence: high
- type: related_to
  target: '[[high-probe-accuracy-does-not-imply-causal-use]]'
  target_id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  confidence: medium
- type: related_to
  target: '[[internal-al-prep-confab-cloud--true-checkpoint]]'
  target_id: paper:internal-al-prep-confab-cloud
  confidence: high
- type: uses
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: uses
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: low
---

## Summary

Amendment AN selected residual confabulations with the confabulation-propensity
sensor (prop_z >= 1.00) and applied an erase-and-write setpoint on the
doubt-orthogonalized caution_perp coordinate, refit on the AI-TRUE checkpoint.
On the numbers the setpoint write did not convert any of the 116 baseline
confabs into refusals, and the reverse push did not release any of the 114
baseline answerable-refused rows. A precision readback confirms the write landed
on-axis (observed setpoint within 0.58 of a sigma-22.13 scale of the commanded
value), so this is not an injection-fidelity failure.

This null is CONFOUNDED and is reported as such, not as a mechanism claim. The
actuator direction was caution_perp refit on the AI-TRUE checkpoint, cosine
-0.064 with AC's validated GRPO-v2 direction: essentially a different, orthogonal
vector. AC's win validated AC's direction as a lever (refined B1: ablation moves
known_refused refusal 0.994 -> 0.524 with specificity); it does NOT establish
that AN's refit direction is a lever, and the positive-control screen that would
have (section 6) was deferred, not run. So the null cannot separate "the caution
axis cannot suppress confabulation" from "this refit direction is a dead
actuator." Crucially, this is NOT evidence for an "input-side actuates,
write-side nulls" rule: AC is itself a write-side erase-write on caution_perp
and it PASSED at +8.7pt. Write-side activation edits are not uniformly null; AC
is the standing counterexample.

## Claims

- Evidence label: pre-registered causal intervention, primary vs permuted-flag
  control (AN-G2/AN-G3, gates_report.json). Primary arm flags 244 rows (47
  confabs, 4 corrects, 11 wrong, 18 answerable-refused, 164
  unanswerable-refused) via prop_z >= 1.00 and pushes g=+2 on the refit
  caution_perp; 0 of 116 baseline confabs killed (floor >= 5, MISS); all 47
  flagged confabs land in confab_to_different_confab. Control arm (uniform
  244-row draw) also kills 0; primary-minus-control diff 0, 1,000-resample row
  bootstrap 95% CI [0.0, 0.0] (floor diff >= 5 with CI excluding zero, MISS).
- Evidence label: collateral gate (AN-G1). 0 of the 4 flagged baseline-correct
  rows flip to refusal under g=+2 (ceiling <= 2, PASS) - but the pass is
  vacuous: with zero effect on the confab population there is necessarily zero
  effect on the correct population it shares a write with, so the honesty
  guarantee this gate was meant to certify was never at stake.
- Evidence label: descriptive dose ladder, gate-free. g=+1 and g=+3 on the same
  47 flagged confabs each kill 0 (no dose-response at any tested gain,
  bounding the AN-G2/G3 null against a linearity assumption).
- Evidence label: descriptive bidirectional arm, gate-free. The same actuator
  pushed g=-2 (setpoint DOWN, toward answering) on the 114 baseline
  answerable-refused rows de-refuses 0 (rate 0.0), with 0 of those becoming
  correct answers - the null holds in both directions of the same write.
- Evidence label: injection-fidelity smoke (smoke_primary/readback.json, 20
  flagged + 8 unflagged rows). Mean observed setpoint on flagged rows 43.98 vs
  commanded 44.26 (max abs error 0.58 against sigma 22.13); unflagged rows show
  zero coordinate shift (mean abs shift 0.0). The write lands precisely on-axis
  and touches only the intended rows; the null is not an artifact of a weak or
  mistargeted push.

## Relevance to experiment

The gate outcomes (AN-G2 and AN-G3 both missing) are real, but their
interpretation is bounded by the confound above: AN used an actuator direction
never validated as a lever on this checkpoint, so it cannot license the claim
that the caution axis is decision-inert for confabulation. The program should
NOT carry forward any "input-side actuates, write-side nulls" taxonomy; that
taxonomy is falsified by AC, a write-side erase-write on caution_perp that
passed at +8.7pt. What AN actually leaves is a sharpened next experiment: first
validate a caution actuator on the AI-TRUE checkpoint (the deferred section 6
positive-control screen), then couple that validated actuator to the
confab-propensity readout exactly as AC coupled the doubt readout to its
validated caution_perp. Until that validation exists, treat AN as one
confounded data point, not as evidence about the caution axis. Single checkpoint
(AI-TRUE), single seed; Tier-2 exploratory, not pooled with the locked Phase 1
matrix.
