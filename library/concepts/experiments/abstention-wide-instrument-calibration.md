---
title: abstention-wide-instrument-calibration
aliases:
- Wide-instrument abstention baseline and placebo calibration (CPU re-read)
- calibration cross-family baseline and placebo re-read
tags:
- kg/experiment
- experiment
- cross-family
- doubt-snap
kg:
  id: experiment:abstention-wide-instrument-calibration
  type: experiment
  status: canonical
related:
- '[[rr2-mistral-adjudicated-refusal-confirm]]'
- '[[qwen35-4b-midband-heldout]]'
- '[[rr-cross-family-raw-refusal]]'
- '[[undosed-wide-instrument-baseline-abstention-is-family-graded]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
- '[[detector-v2-undercounts-baseline-abstention-by-family-varying-margins]]'
- '[[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]'
- '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
- '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
relationships:
- type: builds_on
  target: '[[rr2-mistral-adjudicated-refusal-confirm]]'
  target_id: experiment:rr2-mistral-adjudicated-refusal-confirm
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md (Motivation and posture)
- type: derived_from
  target: '[[qwen35-4b-midband-heldout]]'
  target_id: experiment:qwen35-4b-midband-heldout
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md#design (QH cell source runlogs)
- type: derived_from
  target: '[[rr-cross-family-raw-refusal]]'
  target_id: experiment:rr-cross-family-raw-refusal
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md#design (LB cell source runlogs)
- type: supports
  target: '[[undosed-wide-instrument-baseline-abstention-is-family-graded]]'
  target_id: mechanism:undosed-wide-instrument-baseline-abstention-is-family-graded
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md#outcome (Calibration table)
- type: supports
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md#outcome (Qwen placebo detail; falsifier adjudication)
- type: supports
  target: '[[detector-v2-undercounts-baseline-abstention-by-family-varying-margins]]'
  target_id: mechanism:detector-v2-undercounts-baseline-abstention-by-family-varying-margins
  confidence: high
  evidence:
  - experiments/abstention-wide-instrument-calibration/AMENDMENT.md#outcome (Calibration table, Undercount column)
- type: related_to
  target: '[[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]'
  target_id: mechanism:wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal
  confidence: high
- type: related_to
  target: '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
  target_id: mechanism:random-direction-placebo-recruits-additional-wide-instrument-abstention
  confidence: high
- type: related_to
  target: '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
  target_id: mechanism:canonical-phrase-detector-undercounts-cross-family-abstention-idioms
  confidence: medium
---

Registered confirmatory successor to `rr2-mistral-adjudicated-refusal-confirm`
(resolved falsified 2026-07-13, PR #288), which certified two facts at once
for mistral alone: the wide abstention instrument (detector v2 plus a
blinded adjudication lane) confirms idiom-inclusive refusal a narrow
canonical detector undercounts, and the same wide instrument reveals mistral's
confab pool already abstains at 0.280 undosed, so a placebo tolerance
transcribed from a zero-baseline world fired on a +7.4 point random-direction
lift. This experiment is a CPU-only retrospective re-read of generation text
already on disk under prior harnesses, measuring wide-instrument baseline
abstention and placebo sensitivity for two additional families: qwen (source
runlogs from `qwen35-4b-midband-heldout`) and llama (source rows from
`rr-cross-family-raw-refusal`), against mistral's numbers cited from RR2.

Resolved 2026-07-14, **verdict resolved, falsifier did not fire**. All
numbers were certified by an adversarial red-team review that independently
re-derived every headline rate bit-for-bit from row-level artifacts before
the verdict was written.

- Undosed wide-instrument baseline confab abstention is family-graded, not
  a single constant: qwen 139/1332 = 0.104 [0.089, 0.122], llama 239/1453 =
  0.164 [0.146, 0.184], mistral 368/1312 = 0.280 [0.257, 0.305] (cited)
  ([[undosed-wide-instrument-baseline-abstention-is-family-graded]]).
- A magnitude-matched random_direction placebo shifts wide-instrument
  confab abstention in opposite signs by family: qwen -5.13 points
  (paired, suppression) versus mistral +7.39 points (recruitment, cited)
  ([[random-direction-placebo-response-is-family-specific-in-sign]]).
- Detector v2 undercounts the wide-instrument baseline in every family
  measured, by a family-varying margin: qwen 6.1 points, llama 12.9 points,
  mistral 12.2 points (cited)
  ([[detector-v2-undercounts-baseline-abstention-by-family-varying-margins]]).

The registered falsifier trigger ("placebo delta >= 5 points") is read under
a signed, consequent-coherent interpretation, adopted on the red-team's
independent recommendation: the measured qwen delta is -5.13
(suppression), and the trigger's own stated consequent
("perturbation-recruited hedging") is a claim a suppression contradicts, so
under the signed reading the trigger does not fire. The prediction is not
cleanly confirmed even though the falsifier does not fire: the placebo leg
("below 3 points") is missed in magnitude (5.13 points) despite its
suppressive direction, and the llama baseline leg ("below 0.15") is missed
at 0.164. The QL dose-response cell (qwen ladder, wide-instrument grading)
is terminally voided under its own registered grader-calibration rule and
reported straight as detector-v2-only; this does not touch QH, LB, or MC.

The deliverable is a design rule for successors: a direction-specificity
experiment must not register a flat small symmetric placebo tolerance. The
placebo criterion must be registered against the per-family measured
wide-instrument baseline (qwen 0.104, llama 0.164, mistral 0.280) and must
tolerate several points of non-directional movement in either sign at
matched magnitude. Source of truth:
`experiments/abstention-wide-instrument-calibration/AMENDMENT.md`.
