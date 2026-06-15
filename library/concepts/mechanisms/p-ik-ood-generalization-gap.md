---
aliases:
- P(IK) Generalizes Discriminatively But Not Calibration-Wise OOD
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:p-ik-ood-generalization-gap
  type: mechanism
  status: canonical
cause: Training a [[p-ik]] value-head classifier exclusively on [[triviaqa]] questions and evaluating on arithmetic, Lambada, or code tasks
effect: Decent [[auroc]] discriminability on out-of-distribution tasks but poor [[calibration]] (high [[brier-score]]) when compared to a model trained on all tasks
polarity: enables
related:
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[p-ik]]'
- '[[triviaqa]]'
- '[[auroc]]'
- '[[calibration]]'
- '[[brier-score]]'
relationships:
- type: supported_by
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: related_to
  target: '[[p-ik]]'
  target_id: method:p-ik
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
---

The [[p-ik]] probe can transfer its ranking ability across task types (decent AUROC OOD), suggesting the underlying latent features encoding "I know this" are somewhat general. However, the absolute probability estimates are poorly calibrated OOD because the probe's sigmoid output is tuned to the training task's accuracy distribution. The paper (arXiv:2207.05221) shows this calibration gap (Brier 0.194 vs 0.042 on mixed-arithmetic) and motivates multi-task training of [[p-ik]] probes when calibrated probabilities rather than rankings are needed.
