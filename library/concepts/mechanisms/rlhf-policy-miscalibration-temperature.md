---
aliases:
- RLHF Policy Miscalibration Remediable by Temperature Scaling
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-policy-miscalibration-temperature
  type: mechanism
  status: canonical
cause: '[[reinforcement-learning-from-human-feedback]] finetuning of a language model, which shifts the output distribution'
effect: Apparent miscalibration that can be corrected to near-baseline [[calibration]] quality by applying a simple temperature adjustment, suggesting the underlying representations remain calibrated
polarity: enables
related:
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[calibration]]'
relationships:
- type: supported_by
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
---

RLHF shifts the token probability distribution toward higher-confidence outputs, making the raw logits appear overconfident relative to empirical accuracy. However, because the underlying representations are unchanged, a post-hoc temperature rescaling largely restores calibration. The paper (arXiv:2207.05221) shows that RLHF-induced miscalibration is surface-level rather than fundamental, which has implications for how to measure and correct calibration in aligned models.
