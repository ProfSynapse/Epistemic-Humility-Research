---
title: 'Propensity-Selected, Caution-Actuated Regulator Does Not Reach the Confab Cloud (Amendment AN, TRUE checkpoint)'
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

Amendment AN tested the surviving combination Amendment AL's same-direction
push and Amendment AI's reward-channel test each left open: select residual
confabulations with the sensor that has proven statistical reach into the
confab cloud (the confabulation-propensity direction), then correct them with
the actuator Amendment AC proved moves behavior on its own population (an
erase-and-write setpoint on the doubt-orthogonalized caution_perp coordinate,
refit on the AI-TRUE checkpoint, cos -0.064 to the GRPO-v2 direction it
replaces). The result is a clean null in both directions: the setpoint write
does not convert any of the 116 baseline confabs into refusals, and the same
actuator run in reverse does not release any of the 114 baseline
answerable-refused rows into answers. A precision readback confirms the write
landed on-axis (observed setpoint within 0.58 of a sigma-22.13 scale of the
commanded value), so this is not an injection-fidelity failure: the write is
verified precise and visibly changes the generated text (every flagged confab
becomes a different confab), yet the fabricate-vs-refuse decision itself never
moves. caution_perp is a correlate of the caution behavior it was fit on, not
a general-purpose lever the confab cloud answers to when addressed through a
different sensor. This is the strongest form yet of the program's "reads but
does not actuate" pattern: it closes both the imprecise-injection escape (AL
already ruled this out; AN reconfirms it with a fresh readback) and the
wrong-actuator escape (AC's actuator is independently proven to move
behavior) that earlier write-side nulls left open.

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

Falsifier fired as pre-registered (AN-G2 AND AN-G3 both missing): the caution
setpoint does not reach the confab cloud selectively even when aimed there by
the reaching sensor, so caution_perp joins the correlate pile alongside the
Amendment AL propensity-direction null and the Amendment AI reward-channel
null. The framing distinction the program should carry forward: every WRITE-
side activation-edit tested on an isolated axis so far (AA/AB first-person and
activation injection, AL radial anti-propensity, AI reward-channel coupling,
AN this result) is null, while every INPUT-side / TEXT-channel intervention
tested (AF system-prompt doubt-prime, AC doubt-coupled caution itself, AG
asymmetric compliance) has actuated. AN failing is consistent with, not
contradictory to, those prime-channel wins - it narrows the open question to
why the residual-stream write path stays decision-inert for this behavior
while the same information delivered through the prompt or through the
model's own generated context moves it. Single checkpoint (AI-TRUE), single
seed; Tier-2 exploratory, not pooled with the locked Phase 1 matrix.
