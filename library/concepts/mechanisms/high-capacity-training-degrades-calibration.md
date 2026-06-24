---
aliases:
- capacity-calibration tradeoff
- depth-width miscalibration
- model capacity worsens ECE
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:high-capacity-training-degrades-calibration
  type: mechanism
  status: canonical
cause: "Increasing neural network depth, width, or the use of Batch Normalization during training of classification models, combined with reduced weight decay"
effect: "ECE rises substantially even as classification error falls, because capacity amplifies NLL overfitting and BN reduces the implicit regularization that previously kept confidence from inflating"
polarity: increases
related:
- '[[1706.04599--on-calibration-of-modern-neural-networks]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
- '[[nll-overfitting-degrades-calibration]]'
- '[[model-size-improves-calibration]]'
- '[[temperature-scaling]]'
relationships:
- type: supported_by
  target: '[[1706.04599--on-calibration-of-modern-neural-networks]]'
  target_id: paper:1706.04599
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[nll-overfitting-degrades-calibration]]'
  target_id: mechanism:nll-overfitting-degrades-calibration
  confidence: high
- type: related_to
  target: '[[model-size-improves-calibration]]'
  target_id: mechanism:model-size-improves-calibration
  confidence: high
- type: related_to
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
  confidence: high
---

Guo et al. (arXiv:1706.04599) vary depth (shallow to 110+ layers), width (filters per layer on ResNet-14), normalization (with vs without BN on a 6-layer ConvNet), and weight decay (on ResNet-110) while measuring ECE on CIFAR-100. All four factors show the same qualitative pattern: more capacity or less regularization raises ECE. A 6-layer ConvNet with BN has worse calibration than without BN despite improved accuracy. A ResNet-110 SD reaches ECE 12.67% uncalibrated on CIFAR-100 versus a 5-layer LeNet that is well-calibrated. The finding motivated temperature scaling as a post-hoc remedy and established that modern training trends (deep architectures, BN, low weight decay) are the upstream cause of the miscalibration problem.
