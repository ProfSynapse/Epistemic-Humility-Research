---
aliases:
- CIFAR-10
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:cifar-10
  type: dataset
  status: canonical
area: datasets
related:
- '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
- '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
- '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
- '[[svhn]]'
- '[[out-of-distribution-detection]]'
relationships:
- type: proposed_by
  target: '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
  target_id: paper:1802.04865
  confidence: medium
- type: related_to
  target: '[[svhn]]'
  target_id: dataset:svhn
  confidence: medium
---

CIFAR-10 is a benchmark image-classification dataset of 60,000 32x32 colour
images across 10 object classes (50,000 train / 10,000 test). It is a standard
testbed for confidence estimation, selective prediction, and out-of-distribution
detection in computer vision.

**Why it matters here:** It is the shared evaluation substrate for the
vision-side confidence-head lineage in this library (learned confidence branch,
SelectiveNet, ConfidNet), the prior art whose "trained scalar readout for
selective/failure prediction" shape motivates the experiment's confidence head.

**Lineage:** Krizhevsky 2009; paired with [[svhn]] as an in-distribution /
out-of-distribution pair in confidence and OOD-detection studies.
