---
title: write-direction-naming-battery
aliases:
- 'Write-direction naming battery: what is the mid-band c_hat write, behaviorally?'
- naming battery for the hs20 c_hat write
- unnamed write direction (form instrument void)
tags:
- kg/experiment
- experiment
- doubt-snap
- margin-theory
- naming
kg:
  id: experiment:write-direction-naming-battery
  type: experiment
  status: canonical
related:
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[qwen35-4b-midband-heldout]]'
- '[[margin-mapping]]'
- '[[margin-evidence-responsiveness-worldknown]]'
- '[[gate-contribution-factorial]]'
- '[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]'
- '[[midband-negative-dose-suppresses-refusal-without-restoring-answer]]'
- '[[midband-write-on-knowns-is-difficulty-blind]]'
- '[[midband-write-corrupts-known-answers-more-than-it-produces-abstention]]'
- '[[known-unknown-direction]]'
relationships:
- type: builds_on
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Frozen operating point; c_hat, random_direction, and standardization scalars loaded byte-identical from this experiment's build_manifest.json, no direction refit)
- type: builds_on
  target: '[[qwen35-4b-midband-heldout]]'
  target_id: experiment:qwen35-4b-midband-heldout
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Motivation and posture; this cell behaviorally characterizes the write that produced this experiment's held-out mid-band self-sorting claim)
- type: builds_on
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Prior reads that broke blinding; disclosures D-1 through D-4 computed on M1's committed row logs, re-scoping every arm to unmeasured questions)
- type: builds_on
  target: '[[margin-evidence-responsiveness-worldknown]]'
  target_id: experiment:margin-evidence-responsiveness-worldknown
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Populations; P-REFUSE and P-KNOWN drawn from this experiment's committed qwen35_4b_worldknown_census.jsonl)
- type: related_to
  target: '[[gate-contribution-factorial]]'
  target_id: experiment:gate-contribution-factorial
  confidence: medium
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (What is already governed, item 3; the gate axis falsified in both families is cited as governing context for running every arm ungated)
- type: supports
  target: '[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]'
  target_id: mechanism:form-taxonomy-pattern-battery-underdetects-epistemic-marking
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md#outcome (instrument-void row; core disagreement 86/200 = 0.43 against the 0.05 floor)
- type: supports
  target: '[[midband-negative-dose-suppresses-refusal-without-restoring-answer]]'
  target_id: mechanism:midband-negative-dose-suppresses-refusal-without-restoring-answer
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md#outcome (Axis B, POSITIVE-ONLY via override O-2)
- type: supports
  target: '[[midband-write-on-knowns-is-difficulty-blind]]'
  target_id: mechanism:midband-write-on-knowns-is-difficulty-blind
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md#outcome (Axis K, KNOWLEDGE-STATE)
- type: supports
  target: '[[midband-write-corrupts-known-answers-more-than-it-produces-abstention]]'
  target_id: mechanism:midband-write-corrupts-known-answers-more-than-it-produces-abstention
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md#outcome (O-1's numeric condition fires; ratio 6.37 against the factor-3 line)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Motivation and posture; applies this term's earnability criterion, adjudicated for the read direction by margin-evidence-responsiveness-worldknown, to the write side)
---

Registered exploratory instrument/mechanism-tier cell asking what the
mid-band hs20 `c_hat` write actually does behaviorally, rather than what it
should be called by prior taste. The write was loosely labeled "caution" or
"boundary push" in governed prose; the PI's stated prior was that the honest
name is an abstention/I-don't-know actuator. The cell runs entirely on the
frozen Qwen/Qwen3.5-4B hs20 operating point that carries the held-out
mid-band self-sorting claim (`qwen35-4b-midband-heldout`), not on the
Qwen3-4B/L34 overdrive lineage where the write is already known to be
non-selective. No direction is refit and no gate is applied anywhere; every
row in every arm is dosed, because the write's own selectivity, not the
gate's row targeting, is the object under test (see
`gate-contribution-factorial`, which falsified the gate axis in both
families). Three axes, each resolved by a dedicated arm against a
pre-registered numeric gate, feed an eight-row, pre-stated, exhaustive
outcome-to-name mapping table plus two override rules and an instrument-void
row: axis G (Arm A, is the intermediate-dose output form epistemically marked
or merely degraded, scored by a fresh output-form taxonomy this cell had to
build), axis B (Arm B, does negative dosing specifically release natural
over-refusal, on P-REFUSE rows drawn from `margin-evidence-responsiveness-worldknown`'s
committed census), and axis K (Arm C, does positive dosing on known-correct
rows track retrieval difficulty or is it difficulty-blind, on a fresh,
never-dosed, disjoint PopQA pool). Four disclosures made before sign,
computed on `margin-mapping` (M1)'s committed row logs, re-scoped each arm to
questions not already measured and are recorded as declared inputs rather
than blind predictions.

Resolved 2026-07-30 as **unnamed write direction (form instrument void)**.
The Arm A taxonomy failed its own registered blinded-calibration gate (core
disagreement 86/200 = 0.43 against a 0.05 floor, a one-sided under-detection
of hedged and non-answerability marking:
[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]), so axis G
is unresolved and no naming-table row is assembled; axes B and K are reported
separately per the cell's registered rule. Axis B resolves POSITIVE-ONLY via
override O-2: negative dosing clears the release-magnitude floor decisively
but fails both registered specificity legs, so the finding is recorded as
output-gate suppression rather than abstention control
([[midband-negative-dose-suppresses-refusal-without-restoring-answer]]), the
single outcome that would have earned the PI's candidate abstention-actuator
name and did not. Axis K resolves KNOWLEDGE-STATE: the disclosed exploratory
difficulty gradient does not replicate on a fresh, never-dosed, roughly
five-times-larger pool
([[midband-write-on-knowns-is-difficulty-blind]]). Override O-1 fires on the
same fresh pool at a 6.37:1 wrongness-to-abstention ratio, generalizing a
previously disclosed dissociation beyond the M1 rows it was first read on
([[midband-write-corrupts-known-answers-more-than-it-produces-abstention]]).

The registered prediction (naming-table row 4 with the O-1 prefix,
"answer-corrupting retrieval-suppression gradient") is falsified by two
independent routes: the assembled outcome is the instrument-void row, and
axis K's KNOWLEDGE-STATE resolution excludes row 4 regardless of the void. No
locked verdict moves; this is exploratory instrument/mechanism-tier evidence,
reported separately from the Phase 1 headline matrix. The cell constrains
interpretation of the `c_hat` write (it rules out an earned abstention-actuator
name and rules out treating negative-dose release as specific or the
positive-dose cost on knowns as difficulty-indexed) rather than earning the
write any behavioral name, mentalistic or otherwise. Source of truth:
`experiments/write-direction-naming-battery/AMENDMENT.md`.
