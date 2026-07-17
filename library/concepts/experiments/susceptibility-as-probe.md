---
title: susceptibility-as-probe
aliases:
- 'Susceptibility as probe: margin vs readout vs verbalized confidence'
- M2 susceptibility-as-probe
- readout-plus-margin complementarity test
tags:
- kg/experiment
- experiment
- margin-theory
kg:
  id: experiment:susceptibility-as-probe
  type: experiment
  status: canonical
related:
- '[[margin-mapping]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[commitment-margin]]'
- '[[known-unknown-direction]]'
- '[[qwen-midband-readout-and-susceptibility-channels-are-redundant]]'
- '[[qwen-midband-verbalized-confidence-anti-tracks-answerability]]'
relationships:
- type: builds_on
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design; reuses the 760
    M1 margin rows byte-identically, registered subsample seed 48260714, and
    the censored-row score convention from M1 Decision record item 7)
- type: builds_on
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design; the readout
    score is a fresh projection of the row's hs20 hidden state onto the
    frozen c_hat direction from this lineage, revision 851bf6e8, used
    projection-only with no refit)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Motivation and posture;
    the direct test of framework Claim 3, the readout/susceptibility
    dissociation)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design, Three per-row
    scores; the susceptibility score is the M1 tipping dose, the
    operationalized commitment margin)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design, Three per-row
    scores; the readout score is the projection onto the frozen
    known-unknown direction)
- type: supports
  target: '[[qwen-midband-readout-and-susceptibility-channels-are-redundant]]'
  target_id: mechanism:qwen-midband-readout-and-susceptibility-channels-are-redundant
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md#outcome (Criterion
    verdicts P1 complementarity, P2 head-to-heads, S1 sanity)
- type: supports
  target: '[[qwen-midband-verbalized-confidence-anti-tracks-answerability]]'
  target_id: mechanism:qwen-midband-verbalized-confidence-anti-tracks-answerability
  confidence: medium
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md#outcome (Outcome,
    Descriptives; SC2 void, registered descriptive finding only)
---

Registered head-to-head of three per-row epistemic-state channels on the 760
qwen35_4b rows from the margin-mapping experiment (400 confab, 360
known_correct_answered): a susceptibility score (the M1 commitment margin,
the negative tipping dose along the frozen known-unknown direction), a
readout score (a fresh projection of the row's hs20 hidden state onto the
frozen c_hat direction, no refit), and a verbalized confidence score (one
greedy 0-100 self-report elicitation per row). This is experiment M2 of the
margin-theory cascade (`docs/research/margin-theory-framework.md`, section
4), the direct test of framework Claim 3: that epistemic information exists
in a readout channel and a susceptibility channel that may dissociate. The
primary criterion is complementarity: whether a cross-fitted logistic
combination of readout plus margin beats the readout alone by at least a
registered incremental-AUROC floor.

Resolved 2026-07-17. The S1 sanity gate halted the first analysis pass at
raw-polarity readout AUROC 0.0179; diagnosis found the drafted readout spec
omitted the lineage's own sign convention (c_hat orients raw z
confab-negative), and a PI-approved pre-analysis clarification (readout
score = negative z) was repinned (4dc5722c) before any criterion quantity
was read, so no predictor's call could move. SC2 voided the
verbalized-confidence channel outright: parse rate 0.7684 against the
registered 0.95 floor.

**P1 complementarity: FAIL.** Cross-fitted readout-plus-margin reaches
AUROC 0.9974 against readout-alone 0.9821; incremental AUROC 0.0154
[0.0081, 0.0237], statistically nonzero but below the registered 0.02
floor (robust under a cross-fitted readout-only baseline, increment
0.0161). The registered redundancy falsifier fires: the readout and
susceptibility channels are redundant at this operating point, detailed in
[[qwen-midband-readout-and-susceptibility-channels-are-redundant]]. **P2
head-to-heads:** the readout beats the margin outright (0.9821 vs 0.8504,
paired difference -0.1316 [-0.1588, -0.1045], CI excludes zero); much of
the margin's own discrimination rides on the censoring structure
(censored-excluded sensitivity 0.7242 [0.6446, 0.7988]). **S1 sanity
(post-clarification): PASS**, 0.9821 [0.9730, 0.9900] vs floor 0.80.
Verbalized confidence on the 584 parseable rows is void by SC2 but
descriptively striking: AUROC 0.1479 [0.1214, 0.1754], strongly
anti-predictive (the model verbalizes higher confidence on rows it
confabulates), recorded in
[[qwen-midband-verbalized-confidence-anti-tracks-answerability]].

Predictions scoreboard: the differentiating complementarity slot resolves
FAIL, so the orchestrator's registered call (redundant) is right and the
PI's (complementary) is wrong; both were right that the readout wins the
head-to-head; the confidence slot is void and unscored. Framework
consequence: Claim 3's dissociation reading is rejected at the qwen
mid-band operating point at the registered floor. The readout projection
already carries nearly everything the margin knows about confab-vs-known
here; the margin remains mechanistically meaningful (M1's retrodiction) but
is not an independent detector over the readout at this operating point.
M4 proceeds unchanged; M5 treats the margin as mechanism, not as a second
detector. No locked verdict moves: this is exploratory instrument/mechanism-
tier evidence, reported separately from the Phase 1 headline matrix. Source
of truth: `experiments/susceptibility-as-probe/AMENDMENT.md`.
