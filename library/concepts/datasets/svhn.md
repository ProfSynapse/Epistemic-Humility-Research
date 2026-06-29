---
aliases:
- SVHN
- Street View House Numbers
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:svhn
  type: dataset
  status: canonical
area: datasets
related:
- '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
- '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
- '[[cifar-10]]'
- '[[out-of-distribution-detection]]'
relationships:
- type: proposed_by
  target: '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
  target_id: paper:1802.04865
  confidence: medium
- type: related_to
  target: '[[cifar-10]]'
  target_id: dataset:cifar-10
  confidence: medium
- type: related_to
  target: '[[out-of-distribution-detection]]'
  target_id: term:out-of-distribution-detection
  confidence: medium
---

SVHN (Street View House Numbers) is a benchmark dataset of over 600,000 32x32
colour digit images cropped from Google Street View. In confidence-estimation
work it serves both as a classification benchmark and, paired with CIFAR-10, as
the out-of-distribution set in OOD-detection evaluations.

**Why it matters here:** It is half of the standard CIFAR-10/SVHN in-distribution
vs out-of-distribution pairing used to test whether a trained confidence readout
assigns low confidence to inputs outside its training distribution — the
vision-side analogue of answerability detection.

**Lineage:** Netzer et al. 2011; used as the OOD complement to [[cifar-10]] in
DeVries and Taylor 2018 and SelectiveNet.
