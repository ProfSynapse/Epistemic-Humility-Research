---
title: form-judge-axis-g-rescore
aliases:
- 'Form judge instrument: blinded-lane F1/F2/F3 grading and axis-G rescore of the naming-battery Arm A generations'
- judge-lane axis-G rescore
- form gradedness rescored with a validated blinded judge
tags:
- kg/experiment
- experiment
- doubt-snap
- margin-theory
- naming
kg:
  id: experiment:form-judge-axis-g-rescore
  type: experiment
  status: canonical
related:
- '[[write-direction-naming-battery]]'
- '[[abstention-wide-instrument-calibration]]'
- '[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]'
- '[[blinded-judge-lane-validates-open-class-form-grading]]'
- '[[caution-write-mode-switches-prose-to-explicit-idk]]'
relationships:
- type: builds_on
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md (Motivation and posture; reads
    the naming battery's frozen Arm A generations read-only, re-adjudicating the
    axis it left instrument-void)
- type: derived_from
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md (Motivation and posture;
    the standing blinded sharded adjudication lane, lineage abstention-wide-instrument-calibration,
    RR2, RR3, and the naming battery's own calibration slice, promoted to primary
    instrument)
- type: tests
  target: '[[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]'
  target_id: mechanism:form-taxonomy-pattern-battery-underdetects-epistemic-marking
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md (Motivation and posture;
    re-answers the open axis-G question that mechanism left instrument-void, without
    editing or reopening that resolution)
- type: supports
  target: '[[blinded-judge-lane-validates-open-class-form-grading]]'
  target_id: mechanism:blinded-judge-lane-validates-open-class-form-grading
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md#outcome (Instrument validation;
    G1 PASS 0.035, G2 PASS 25/25)
- type: supports
  target: '[[caution-write-mode-switches-prose-to-explicit-idk]]'
  target_id: mechanism:caution-write-mode-switches-prose-to-explicit-idk
  confidence: high
  evidence:
  - experiments/form-judge-axis-g-rescore/AMENDMENT.md#outcome (Axis-G rescore;
    baseline share 0.431 falling monotonically with dose, F4 16 to 267)
---

Exploratory instrument-plus-rescore cell that re-answers the naming battery's
open axis-G question (is the mid-band `c_hat` write's intermediate-dose output
epistemically graded or merely degraded?) after that cell's own regex form
taxonomy failed blinded calibration and voided the axis
([[form-taxonomy-pattern-battery-underdetects-epistemic-marking]]). Rather than
patching the voided pattern classifier, the program's standing blinded sharded
adjudication lane (a single context-free opus-tier subagent judge per shard,
isolated from the model that produced the graded text, plus an independent
second isolated model adjudicator for calibration) is promoted to primary
instrument for the open-class F1/F2/F3 boundary; the closed-class F4/F5 screens
stay the validated deterministic detectors they already were. The cell reads
only the naming battery's frozen 2800 Arm A generations, read-only, no
generation and no GPU; the original axis-G thresholds (F2+F3 share above 0.15
at an intermediate dose AND at least +0.10 over baseline) are re-registered
unchanged so the rescore answers the original question rather than a moved one.

Resolved 2026-07-31. A first calibration attempt was ruled VOID pre-unblind at
the registered lead spot-check: the clear-negative decoy source (Arm C
`correct_v2` rows) retains no generation text anywhere on disk, so the pool
builder silently substituted empty strings for all 25 clear-negative decoys.
No gate was computed and no grades were used; a PI-approved governed deviation
dropped the clear-negative decoy lane (G2 gates clear-positive decoy agreement
only) and a fail-closed empty-text guard was added before a second attempt.

Calibration attempt 2 (seed 20260801) validated the instrument on both
registered gates: G1 three-way judge-vs-independent-adjudicator disagreement
7/200 = 0.035 against a 0.12 floor (dev-set judge-vs-judge disagreement 0.080
plus a 0.04 headroom margin), and G2 clear-positive decoy agreement 25/25 =
1.00 against a 0.92 floor; a registered lead spot-check (n=30) was concordant
with the rubric and a non-gating stability regrade showed 4/57 = 0.070
borderline F1/F2 flips
([[blinded-judge-lane-validates-open-class-form-grading]]).

With the instrument validated, the axis-G payload (all 1781 non-spent
screened-in rows across the 7 Arm A sub-arms) resolved BINARY: the 0.15
intermediate-dose share floor clears at all three intermediate doses, but the
+0.10-over-baseline leg fails at every dose because the validated judge finds
substantially more baseline hedging (0.431) than the voided regex taxonomy
ever detected, and dosing monotonically converts prose output (committed or
hedged alike) into explicit IDK rather than producing a graded intermediate
([[caution-write-mode-switches-prose-to-explicit-idk]]). Both the
orchestrator's and the user's pre-registered predictions (aligned at sign) are
CONFIRMED on outcome and mechanism. This cell does not reopen or soften the
naming battery's own instrument-void resolution, which stands permanently as
that cell's outcome; the naming battery's eight-row outcome-to-name table is
still not assembled from these numbers. Source of truth:
`experiments/form-judge-axis-g-rescore/AMENDMENT.md`.
