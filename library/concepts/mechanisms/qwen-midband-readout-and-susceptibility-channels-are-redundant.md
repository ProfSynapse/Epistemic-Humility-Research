---
title: qwen-midband-readout-and-susceptibility-channels-are-redundant
aliases:
- readout and susceptibility channels are redundant at the qwen mid-band operating point
- Claim 3 complementarity falsified: incremental AUROC 0.0154 vs floor 0.02 (qwen mid-band)
- margin-theory Claim 3 falsified at the qwen mid-band operating point
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen-midband-readout-and-susceptibility-channels-are-redundant
  type: mechanism
  status: canonical
cause: "In the susceptibility-as-probe experiment (M2), a 5-fold cross-fitted logistic combination of the frozen hs20 c_hat readout projection (fold seed 48260718) plus the M1 per-row commitment margin (the susceptibility score, from the same 760-row qwen35_4b population as margin-mapping: 400 confab rows, 360 known_correct_answered rows) was compared against the readout alone for discriminating confab from known_correct_answered, against the registered incremental-AUROC floor of 0.02 (Hanley-McNeil-derived at this sample size)."
effect: "The combination reaches AUROC 0.9974 against readout-alone AUROC 0.9821 (post sign-clarification, negative-z convention); the incremental AUROC is 0.0154 with bootstrap 95% CI [0.0081, 0.0237] (10000 resamples, seed 48260717). The increment is statistically nonzero but sits below the registered 0.02 floor, and stays below it under a cross-fitted readout-only baseline construction (increment 0.0161). The registered redundancy falsifier fires: framework Claim 3's dissociation reading, that the susceptibility channel carries epistemic information the readout channel misses, is falsified at the qwen mid-band operating point. The head-to-head sharpens the picture: the readout alone beats the susceptibility channel outright (0.9821 vs 0.8504, paired difference -0.1316 [-0.1588, -0.1045], CI excludes zero), and much of the margin's own discrimination rides on the censoring structure (censored-excluded sensitivity drops to 0.7242 [0.6446, 0.7988]). The margin remains mechanistically real (M1's retrodiction and setpoint placement both passed) but is not an independent detector over the frozen readout projection at this operating point."
polarity: complicates
related:
- '[[susceptibility-as-probe]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[commitment-margin]]'
- '[[known-unknown-direction]]'
- '[[margin-mapping]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[qwen-midband-commitment-margins-miss-separation-floor]]'
- '[[qwen-midband-verbalized-confidence-anti-tracks-answerability]]'
relationships:
- type: supported_by
  target: '[[susceptibility-as-probe]]'
  target_id: experiment:susceptibility-as-probe
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md#outcome (Criterion
    verdicts P1 complementarity, P2 head-to-heads, S1 sanity)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 3)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design, Three per-row
    scores; the susceptibility score is the operationalized commitment
    margin)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design, Three per-row
    scores; the readout score is the projection onto the frozen
    known-unknown direction)
- type: related_to
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design; the 760 scored
    rows and the censored-row convention are M1's margin dataset)
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Design; the readout
    score reuses the frozen hs20 c_hat direction from this lineage,
    projection-only, no refit)
- type: related_to
  target: '[[qwen-midband-commitment-margins-miss-separation-floor]]'
  target_id: mechanism:qwen-midband-commitment-margins-miss-separation-floor
  confidence: medium
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md (Motivation and posture;
    M2 measures whether the M1 margins, already shown real and correctly
    placed, add usable information over the readout)
- type: related_to
  target: '[[qwen-midband-verbalized-confidence-anti-tracks-answerability]]'
  target_id: mechanism:qwen-midband-verbalized-confidence-anti-tracks-answerability
  confidence: medium
  evidence:
  - experiments/susceptibility-as-probe/AMENDMENT.md#outcome (Outcome; both
    findings come from the same M2 scoreboard on the same 760 rows)
---

The susceptibility-as-probe experiment gives margin theory's Claim 3 its
first direct test, and the result is a clean redundancy: the frozen hs20
readout projection alone already discriminates confab from
known_correct_answered rows at AUROC 0.9821, and adding the per-row
commitment margin through a cross-fitted logistic combination buys an
incremental AUROC of only 0.0154, a real but sub-floor gain against the
registered 0.02 floor. The margin is not inert; the increment's confidence
interval excludes zero, and the margin alone still separates the two
populations at AUROC 0.8504. But the specific claim under test, that the
susceptibility channel carries epistemic information the readout channel
misses, is what the registered floor is built to detect, and it does not
clear it here.

**Why it matters here:** this falsification followed an instrument event
worth recording alongside the result. The S1 sanity gate halted the first
analysis pass at a raw-polarity readout AUROC of 0.0179, a near-inverted
score that flagged a wiring defect rather than a real finding. Diagnosis
traced it to an omission in the drafted readout spec: the frozen c_hat
direction orients raw z confab-negative under its own lineage convention,
which the M2 cell config had not carried forward. A PI-approved
pre-analysis clarification (readout score = negative z) was repinned before
any criterion quantity was read, so the fix could not move any registered
predictor's call; every criterion in this experiment is sign-invariant by
construction. Once repinned, the readout's own discrimination turned out to
be far higher than the margin's, which is what makes the combination's
increment so hard to clear: there is little room left for the margin to add
when the readout alone is already at 0.9821. This is the first falsification
inside the margin-theory cascade after M1's narrow miss on Claim 1
(`docs/research/margin-theory-framework.md`, section 4), and it narrows the
cascade's remaining open question to whether the margin has independent
value anywhere else in the program (M4's naming test, M5's training bridge)
rather than at this operating point.

**Lineage:** first empirical test of Claim 3 in
[[margin-theory-of-epistemic-state]], introduced 2026-07-16 in
`docs/research/margin-theory-framework.md`. Reuses the 760-row margin
dataset and censored-row convention from [[margin-mapping]] (M1) and the
frozen c_hat direction from [[qwen35-4b-midband-doubt-snap]]. Source of
truth: `experiments/susceptibility-as-probe/AMENDMENT.md`, Outcome section,
resolved 2026-07-17.
