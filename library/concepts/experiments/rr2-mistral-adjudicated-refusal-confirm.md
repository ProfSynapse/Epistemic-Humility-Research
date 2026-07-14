---
title: rr2-mistral-adjudicated-refusal-confirm
aliases:
- 'RR2: mistral confirmatory with detector v2 + blinded adjudication lane'
- rr2-mistral-adjudicated-refusal-confirm
tags:
- kg/experiment
- experiment
- cross-family
- doubt-snap
kg:
  id: experiment:rr2-mistral-adjudicated-refusal-confirm
  type: experiment
  status: canonical
related:
- '[[rr-cross-family-raw-refusal]]'
- '[[qwen35-4b-midband-heldout]]'
- '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
- '[[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]'
- '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
relationships:
- type: builds_on
  target: '[[rr-cross-family-raw-refusal]]'
  target_id: experiment:rr-cross-family-raw-refusal
  confidence: high
  evidence:
  - experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md (Motivation and posture; Design)
- type: different_from
  target: '[[qwen35-4b-midband-heldout]]'
  target_id: experiment:qwen35-4b-midband-heldout
  confidence: high
  evidence:
  - experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md#outcome (RG3 placebo fail)
  - experiments/qwen35-4b-midband-heldout/AMENDMENT.md#outcome (RG3(i)/placebo pass)
- type: supports
  target: '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
  target_id: mechanism:canonical-phrase-detector-undercounts-cross-family-abstention-idioms
  confidence: high
  evidence:
  - experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md#outcome (RG1 pass, confirmatory blinded replication of the RR detector-width caveat)
- type: supports
  target: '[[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]'
  target_id: mechanism:wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal
  confidence: high
  evidence:
  - experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md#outcome (RG3 gate results)
- type: supports
  target: '[[random-direction-placebo-recruits-additional-wide-instrument-abstention]]'
  target_id: mechanism:random-direction-placebo-recruits-additional-wide-instrument-abstention
  confidence: high
  evidence:
  - experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md#outcome (RG3 fail, red-team certified)
---

Registered confirmatory successor to the mistral leg of
`rr-cross-family-raw-refusal` (falsified shape F, PR #285): that experiment's
mistral miss carried a binding caveat that the near-miss (refused 0.5793
against the 0.60 floor) was substantially a canonical-3-phrase-detector
coverage gap, established by an unblinded, exploratory hand-recount that
could not itself upgrade the RR verdict. This experiment is the
pre-registered, blinded test of that caveat: same substrate, site, write,
and fixed operating point (hs16, dose 12 sigma_c, RR's own FIT-selected
rung, not refit), scored on fresh held-out rows with two new registered
instruments -- a detector v2 pattern screen (reported, does not gate) and a
primary blinded adjudication lane (labels stripped, decoys mixed in,
seeded shuffle, graded once by a context-free agent against a registered
rubric, hashed before unblinding). It also implements a PI directive
requiring a bounded, blinded human-adjudication lane wherever abstention is
graded, alongside any automatic detector.

Resolved 2026-07-13, **verdict FALSIFIED, on the RG3 placebo leg alone**;
RG1 and RG2 pass. The falsifier fire was certified by an adversarial
red-team review across five surfaces (unblinding/join integrity, decoy
grader-calibration audit, an independent re-read of all baseline-credited
texts, a well-formedness check on the random-arm credits, and a gate-text
audit) before the verdict was recorded.

- **RG1 (benefit): PASS.** Held-out fired-confab adjudicated refusal
  911/1303 = 0.699, Wilson 95% [0.674, 0.723], well above the 0.60 floor
  (LCB 0.674 > 0.50); well-formed 0.987 against the 0.80 floor. This
  confirms the RR detector-width caveat under a blinded, symmetric
  instrument: mistral does express idiom-inclusive refusal at the
  credited-recount level
  ([[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]).
- **RG2 (cost): PASS.** Known-correct adjudicated false refusal 2/382 =
  0.0052, UCB 0.019 against the 0.05/0.10 floor, byte-identical across the
  baseline, gated, and random arms.
- **RG3 (placebo): FAIL.** Baseline (undosed) adjudicated abstention
  reaches 368/1312 = 0.280 on the fired-confab population
  ([[wide-abstention-instrument-reveals-substantial-undosed-baseline-refusal]]),
  and the random_direction placebo lifts that to 465/1312 = 0.354, a +7.39
  point delta against the registered 2-point no-op tolerance
  ([[random-direction-placebo-recruits-additional-wide-instrument-abstention]]).
  The known-correct population shows no such shift (delta 0.0).

Interpretation: the two registered questions decompose cleanly. Is the RR
detector-width caveat real? Yes, confirmed under a blinded instrument at
0.699. Is the effect direction-specific? No, per the registered tolerance:
the wide instrument reveals this confab pool already abstains at 28% via
hedge idioms a narrow detector never counted, and a magnitude-matched
random direction recruits +7.4 points more of the same. The gated write's
own lift over baseline (+41.9 points) is 5.7 times the placebo's, but RG3
is a fixed-tolerance test on the delta, not a ratio test, and it fails as
registered.

This is a contrasting result to `qwen35-4b-midband-heldout` (shape A,
resolved 2026-07-13): that held-out promotion passed its own placebo leg
(random_direction a no-op relative to baseline, delta 0.008) under its
narrower instrument, while this cross-family confirmatory fails its placebo
leg once measured under the wide, idiom-inclusive instrument the RR
detector-width caveat required. Both results stand as registered; neither
is rescored against the other's instrument. Source of truth:
`experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md`.
