---
title: llama-hs17-wide-instrument-rescore
aliases:
- Llama hs17 wide-instrument regeneration and re-score
- llama direction-specificity instrument-robustness closure
tags:
- kg/experiment
- experiment
- cross-family
- j-space
- doubt-snap
kg:
  id: experiment:llama-hs17-wide-instrument-rescore
  type: experiment
  status: canonical
related:
- '[[llama-hs17-direction-specificity]]'
- '[[abstention-wide-instrument-calibration]]'
- '[[qwen3-4b-l34-placebo-seed-census]]'
- '[[wide-instrument-control-rescore]]'
- '[[llama-hs17-direction-specificity-survives-wide-instrument]]'
- '[[llama-hs17-write-is-direction-specific]]'
- '[[known-unknown-direction]]'
- '[[activation-steering]]'
- '[[abstention]]'
relationships:
- type: builds_on
  target: '[[llama-hs17-direction-specificity]]'
  target_id: experiment:llama-hs17-direction-specificity
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Design;
    reuses the frozen hs17 write, gate, dose, and fifteen random-direction
    seeds byte-identically from that resolved cell; regenerates rather than
    re-scores because the resolved cell's harness persisted grades only, no
    generation text)
- type: builds_on
  target: '[[abstention-wide-instrument-calibration]]'
  target_id: experiment:abstention-wide-instrument-calibration
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Instruments;
    the wide two-instrument stack, detector_v2 plus blinded context-free
    adjudication, is pinned hash-identical from this experiment's committed
    pins, no component refit)
- type: related_to
  target: '[[qwen3-4b-l34-placebo-seed-census]]'
  target_id: experiment:qwen3-4b-l34-placebo-seed-census
  confidence: medium
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Motivation
    and posture; mirrors what this experiment did for qwen's late site, now
    for llama's mid-band site)
- type: related_to
  target: '[[wide-instrument-control-rescore]]'
  target_id: experiment:wide-instrument-control-rescore
  confidence: medium
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Motivation
    and posture; the program's original wide-instrument closure precedent
    for qwen's Section 4.5/4.6 controls)
- type: supports
  target: '[[llama-hs17-direction-specificity-survives-wide-instrument]]'
  target_id: mechanism:llama-hs17-direction-specificity-survives-wide-instrument
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md#outcome
    (WR-G1, WR-G2, WR-G3)
- type: related_to
  target: '[[llama-hs17-write-is-direction-specific]]'
  target_id: mechanism:llama-hs17-write-is-direction-specific
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Motivation
    and posture; the narrow-instrument finding this experiment extends to
    the wide instrument)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md (Design;
    reuses the frozen hs17 known-unknown gate and c_hat caution write
    direction verbatim from the parent cell)
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

Exploratory cell on raw-base `unsloth/Llama-3.2-3B-Instruct`, closing the
instrument-scope gap paper 5 SS4.8 and SS6.5 named for llama's hs17
direction-specificity claim: `llama-hs17-direction-specificity` had verified
the mid-band gated write's replication and direction-specificity only under
the narrow `clean_tighten` phrase detector, and a direct re-score of its run
logs was impossible because that harness persisted grades only, not
generation text. This cell regenerates the frozen operating point (same
write, gate, dose, and fifteen random-direction seeds 910001-910015) with a
text-persisting harness and scores the fresh generations under both the
narrow instrument (a bridge check) and the program's wide two-instrument
stack (detector_v2 OR-joined with blinded context-free adjudication, pinned
identical to `abstention-wide-instrument-calibration`).

Resolved 2026-08-26, Outcome A, wide replicates and specific; both
predictors (orchestrator and user) were on record for this outcome.
WR-G1 (regeneration bridge): arm-1 narrow `clean_tighten` 637/872 = 0.7305,
Wilson [0.7001, 0.7589], PASS against the 0.50 floor, the third consistent
sample of this operating point (parent 0.7420, resolved narrow cell 0.7282,
this regeneration 0.7305). WR-G2 (wide replication, primary): arm0 wide
136/872 = 0.1560, arm1 wide 687/872 = 0.7878, net wide lift 0.6319, PASS
against the 0.30 floor. WR-G3 (wide direction-specificity, primary): effect
ratio 0.6319 / 0.0677 (max abs random lift, seed 910005) = 9.34, PASS
against the 3.0 floor; the fifteen-seed random census is centered near zero
under the wide instrument (6 positive / 8 negative / 1 zero, median
-0.0092), matching the narrow census's own centering (ratio 8.25). WR-G4
(known-correct cost) is NOT-ADJUDICABLE as pre-stated: the KU gate fired on
0 of 334 held-out known-correct rows, below the 22-row adjudicability floor.
CG1 (grader calibration) PASS on all 19 adjudication shards at attempt 1,
pooled clear-positive 534/691 = 0.7728.

A run-log anomaly is recorded straight and changes no number: the arm-0 log
contained 25 duplicated confab row_keys (897 lines / 872 unique,
crash-resume overlap); duplicate lines agreed on every detector flag, and
the 24 detector-negative duplicates entered the blinded pool twice under
independent ids, with the two context-free graders agreeing on 24/24 of
them, an unplanned inter-grader reliability check. All registered gates use
the 872 unique row_keys. Llama's hs17 direction-specificity is
instrument-robust, mirroring the precedent `wide-instrument-control-rescore`
and `qwen3-4b-l34-placebo-seed-census` set for qwen's late site. Source of
truth: `experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md`.
