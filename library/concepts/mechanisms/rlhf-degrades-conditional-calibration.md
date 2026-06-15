---
aliases:
- RLHF degrades conditional probability calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-degrades-conditional-calibration
  type: mechanism
  status: canonical
cause: Fine-tuning a language model with [[reinforcement-learning-from-human-feedback]]
effect: Conditional token probabilities become poorly calibrated relative to the base model
polarity: increases
related:
- '[[2305.14975--just-ask-for-calibration]]'
- '[[reinforcement-learning-from-human-feedback]]'
relationships:
- type: supported_by
  target: '[[2305.14975--just-ask-for-calibration]]'
  target_id: paper:2305.14975
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
---

RLHF reward optimization pushes the policy toward responses humans prefer, which typically means more confident, fluent, and definitive outputs. This distributional shift makes the token-level probabilities overconfident relative to empirical accuracy, degrading [[calibration]]. The just-ask-for-calibration paper (arXiv:2305.14975) documents this degradation across ChatGPT, GPT-4, and Claude, and shows that [[verbalized-confidence]] can largely recover calibration that logit-based methods lose.
