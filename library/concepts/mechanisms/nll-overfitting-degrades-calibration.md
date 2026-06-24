---
aliases:
- NLL overfitting
- cross-entropy overfitting degrades calibration
- NLL-accuracy decoupling
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:nll-overfitting-degrades-calibration
  type: mechanism
  status: canonical
cause: "Continued training with cross-entropy loss after test classification error has plateaued, in a high-capacity model with insufficient regularization"
effect: "Test NLL continues to fall (model becomes more confident) while calibration worsens, because the model inflates predicted probabilities beyond what accuracy justifies"
polarity: decreases
related:
- '[[1706.04599--on-calibration-of-modern-neural-networks]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
- '[[cross-entropy-calibration-couples-to-hallucination]]'
- '[[high-capacity-training-degrades-calibration]]'
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
  target: '[[cross-entropy-calibration-couples-to-hallucination]]'
  target_id: mechanism:cross-entropy-calibration-couples-to-hallucination
  confidence: high
- type: related_to
  target: '[[high-capacity-training-degrades-calibration]]'
  target_id: mechanism:high-capacity-training-degrades-calibration
  confidence: high
- type: related_to
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
  confidence: high
---

After a learning-rate drop, both NLL and error improve together; but in subsequent epochs only NLL improves further while classification error changes little (dropping only from 29% to 27% on CIFAR-100 in the NLL-overfitting region). The model learns to assign higher confidence to its predictions without becoming more accurate, producing systematic overconfidence. This mechanism explains why modern high-capacity networks (ResNets, DenseNets) are more miscalibrated than older shallow networks: they have enough capacity to fit NLL without fitting the 0/1 loss. Guo et al. (arXiv:1706.04599) document this in Figure 3 and Section 3 and treat it as the root cause of the miscalibration observed in Table 1.
