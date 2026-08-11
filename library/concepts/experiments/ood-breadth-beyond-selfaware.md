---
title: ood-breadth-beyond-selfaware
aliases:
- OOD breadth beyond SelfAware
- item 26 (paper-3 limitations burn-down)
- paper-3 SelfAware-only OOD limitation resolution
tags:
- kg/experiment
- experiment
- epistemic-humility
kg:
  id: experiment:ood-breadth-beyond-selfaware
  type: experiment
  status: canonical
related:
- '[[selfaware]]'
- '[[known-unknown-direction]]'
- '[[answerability-subspace]]'
- '[[known-unknowns-taxonomy]]'
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[grpo-three-seed-confirmatory]]'
- '[[rawbase-ambigqa-boundary-readout]]'
- '[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]'
- '[[ambigqa-stated-confidence-collapse-not-universal-across-arms]]'
relationships:
- type: builds_on
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "AMENDMENT.md Why this design is front-loaded with screens (the G0 disjointness
    screen is the direct response to the SelfAware training/dev-split contamination
    recorded in grpo-three-seed-confirmatory/NOTEBOOK.md lines 1835-1839)"
- type: evaluates_on
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: high
  evidence:
  - "AMENDMENT.md Motivation and posture (re-runs paper 3's SelfAware behavior and
    stated-calibration panel as the fixed comparator every new surface is scored
    against)"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - "AMENDMENT.md Internal panel (the G7 internal known-unknown readout is the
    frozen L35, anchor-position readout of this direction)"
- type: related_to
  target: '[[answerability-subspace]]'
  target_id: term:answerability-subspace
  confidence: medium
  evidence:
  - "AMENDMENT.md Internal panel (reads the AmbigQA answerability boundary at the
    same locus that separates SelfAware known from unknown)"
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: medium
  evidence:
  - "AMENDMENT.md Limitations (construct heterogeneity across surfaces; AmbigQA's
    ambiguity construct vs SelfAware/KUQ's unknowable-to-anyone construct)"
- type: related_to
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
  evidence:
  - "AMENDMENT.md Motivation and posture (paper 3 manuscript lines 1027-1029,
    the SelfAware-only OOD limitation, and the internal-vs-stated headline gap
    this cell re-tests on new surfaces)"
- type: related_to
  target: '[[rawbase-ambigqa-boundary-readout]]'
  target_id: experiment:rawbase-ambigqa-boundary-readout
  confidence: high
  evidence:
  - "rawbase-ambigqa-boundary-readout/AMENDMENT.md Question (the raw-base cell is
    the direct follow-on fork this experiment's G7 FAIL opened, PI-stated
    2026-08-09)"
- type: supports
  target: '[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]'
  target_id: mechanism:ambigqa-internal-readout-does-not-transfer-from-selfaware
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-09T16:45Z Stage 8 (G7 FAIL both internal-panel arms,
    0.6279/0.6349 vs the 0.90 floor)"
- type: supports
  target: '[[ambigqa-stated-confidence-collapse-not-universal-across-arms]]'
  target_id: mechanism:ambigqa-stated-confidence-collapse-not-universal-across-arms
  confidence: high
  evidence:
  - "NOTEBOOK.md 2026-08-09T16:45Z Stage 8 (G5 FAIL: A3 std 0.1687, A8 std 0.4238
    exceed the 0.10 ceiling)"
---

Tier-2 exploratory amendment resolving paper-3 limitations-burn-down item 26
(manuscript lines 1027-1029: "SelfAware-only OOD surface"). Re-runs paper 3's
behavior panel, stated-calibration panel, and internal known-unknown readout on
eight checkpoints across three additional known/unknown surfaces (KUQ, AmbigQA,
BIG-bench known-unknowns), with a fail-closed G0 disjointness screen (169 KUQ
training-pool hits and 220 KUQ/SelfAware-overlap hits removed) built as the
direct response to the SelfAware training/dev-split contamination found in
`grpo-three-seed-confirmatory`.

Resolved 2026-08-09. **G1 FAIL** (registered): the re-merged answer-supervised
base misses SelfAware reproduction tolerance, voiding arms A2/A6/A7; the cell
reports on five arms (A1/A3/A4/A5/A8). **G2, G3, G_docker PASS.** **G4
NOT_RUN as registered**: gates.yaml derives the 0.70 rank-transfer threshold
from an eight-arm instrument, and after the registered G1 consequence only
five arms exist, so `no_goalpost_movement` forbids re-deriving a five-arm
threshold; unregistered descriptive Spearman rho (~0.10 KUQ, ~0.20 AmbigQA)
is noise-dominated and carries no gate weight.

**G5 FAIL**, detailed in
[[ambigqa-stated-confidence-collapse-not-universal-across-arms]]: two of five
surviving arms (A3, A8) exceed the emitted-std ceiling on AmbigQA, so paper
3's stated-confidence collapse is not universal off SelfAware.

**G7 FAIL on both internal-panel arms**, detailed in
[[ambigqa-internal-readout-does-not-transfer-from-selfaware]]: held-out probe
AUROC 0.6279 (A1) and 0.6349 (A4) against a 0.90 floor, versus 0.9968/0.9971
on SelfAware for the same two checkpoints.

**Falsifier does not fire** (requires >=2 arms at emitted AUROC >=0.70 with
std >0.15; the two high-std arms rank below chance, 0.3953 and 0.3588).
Prediction scoring on the four registered components: P1 (unknown-side rank
transfer) NOT ADJUDICABLE (G4 NOT_RUN); P2 (stated-collapse transfers
unchanged) FAILED (G5); P3 (internal readout separates AmbigQA at >=0.90)
FAILED (G7); P4 (answer-supervision dissociation keeps its sign) SUPPORTED.

**Headline:** behavior transfers in level and known-side over-refusal moves
as predicted, but paper 3's near-perfect internal known-unknown readout does
NOT transfer to the AmbigQA answerability boundary, and the stated-confidence
collapse is not universal on the new surface. This directly opened the fork
resolved by [[rawbase-ambigqa-boundary-readout]]: is the AmbigQA non-transfer
a property of the pretrained representation, or a training-induced warp?

Source of truth: `experiments/ood-breadth-beyond-selfaware/AMENDMENT.md`,
`gates.yaml`, `experiment.yaml`, and `NOTEBOOK.md` (Stage 8 entry,
2026-08-09T16:45Z).
