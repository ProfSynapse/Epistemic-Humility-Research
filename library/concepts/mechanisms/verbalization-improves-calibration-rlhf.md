---
aliases:
- Verbalization recovers calibration in RLHF-LMs
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:verbalization-improves-calibration-rlhf
  type: mechanism
  status: canonical
cause: Prompting an RLHF-LM to express its confidence as output tokens ([[verbalized-confidence]]) rather than reading off conditional probabilities
effect: '[[expected-calibration-error]] is reduced, often by ~50% relative, across ChatGPT, GPT-4, and Claude on [[triviaqa]], [[sciq]], and [[truthfulqa]]'
polarity: decreases
related:
- '[[2305.14975--just-ask-for-calibration]]'
- '[[verbalized-confidence]]'
- '[[expected-calibration-error]]'
- '[[triviaqa]]'
- '[[sciq]]'
- '[[truthfulqa]]'
relationships:
- type: supported_by
  target: '[[2305.14975--just-ask-for-calibration]]'
  target_id: paper:2305.14975
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
- type: related_to
  target: '[[sciq]]'
  target_id: dataset:sciq
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
---

RLHF-trained models retain internal representations that are predictive of answer correctness even after their output distribution shifts to be overconfident. Asking the model to verbalize its confidence elicits these representations as tokens, bypassing the miscalibrated logit layer. The just-ask-for-calibration paper (arXiv:2305.14975) demonstrates roughly 50% relative ECE reductions across major RLHF-trained models using this approach, validating verbalization as a practical calibration recovery technique.
