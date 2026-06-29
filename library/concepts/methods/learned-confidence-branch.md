---
aliases:
- Learned Confidence Branch
- learned confidence estimation
- confidence branch (DeVries-Taylor)
tags:
- kg/method
- concept
- method
kg:
  id: method:learned-confidence-branch
  type: method
  status: canonical
area: methods
related:
- '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
- '[[out-of-distribution-detection]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[confidnet]]'
relationships:
- type: proposed_by
  target: '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
  target_id: paper:1802.04865
  confidence: high
- type: related_to
  target: '[[out-of-distribution-detection]]'
  target_id: term:out-of-distribution-detection
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[confidnet]]'
  target_id: method:confidnet
  confidence: medium
---

An auxiliary confidence-estimation branch added alongside a classifier's
prediction head: a small head outputs a single sigmoid scalar `c` interpreted as
the network's confidence in its prediction. During training the model may
interpolate its softmax prediction toward the ground-truth label in proportion
to `c` (a "hint" whose budget is penalized by a `-log(c)` loss with a dynamically
adjusted weight `beta`), so the network is incentivized to ask for hints only on
hard inputs and thereby learns a calibrated confidence signal.

**Why it matters here:** This is an early, direct instance of a trained scalar
readout head whose output is a usable confidence estimate — the same shape as the
aux_head confidence readout in the experiment. It establishes the "extra head +
proper-scoring-style loss yields a calibrated scalar" pattern.

**Lineage:** DeVries and Taylor 2018; precursor to [[confidnet]] (which regresses
the true-class probability instead of using a hint budget) and to learned
selective-prediction heads such as [[selectivenet]].
