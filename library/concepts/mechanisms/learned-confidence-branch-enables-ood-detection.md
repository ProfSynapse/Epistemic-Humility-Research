---
aliases:
- A learned confidence branch enables out-of-distribution detection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:learned-confidence-branch-enables-ood-detection
  type: mechanism
  status: canonical
cause: "Adding an auxiliary confidence branch trained with a hint-budget / -log(c) objective so the network requests label hints only on hard inputs."
effect: "The learned confidence scalar is low on out-of-distribution and misclassified inputs, enabling competitive OOD detection without OOD training data."
polarity: enables
related:
- '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
- '[[learned-confidence-branch]]'
- '[[out-of-distribution-detection]]'
relationships:
- type: supported_by
  target: '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
  target_id: paper:1802.04865
  confidence: high
- type: related_to
  target: '[[learned-confidence-branch]]'
  target_id: method:learned-confidence-branch
  confidence: high
- type: related_to
  target: '[[out-of-distribution-detection]]'
  target_id: term:out-of-distribution-detection
  confidence: high
---

DeVries and Taylor 2018 show that a network trained to emit a confidence scalar
via a hint budget assigns systematically lower confidence to out-of-distribution
and misclassified inputs, so thresholding the learned scalar matches or beats
max-softmax OOD-detection baselines on CIFAR-10/SVHN-style in/out pairs without
ever training on OOD examples.
