---
aliases:
- Self-prediction training improves behavioral calibration
- Self-reports recover a model's response distribution
- Mode-only self-training yields calibrated behavioral forecasts
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-prediction-training-improves-behavioral-calibration
  type: mechanism
  status: canonical
cause: "A model receives self-prediction training only on its temperature-zero modal behavior."
effect: "On held-out prompts, its sampled hypothetical predictions better match its full object-level response distribution than untrained or cross-trained predictions."
polarity: increases
related:
- '[[2410.13787--looking-inward-language-models-can-learn-about]]'
- '[[self-prediction-training]]'
- '[[mean-absolute-deviation-calibration-error]]'
relationships:
- type: supported_by
  target: '[[2410.13787--looking-inward-language-models-can-learn-about]]'
  target_id: paper:2410.13787
  confidence: medium
- type: related_to
  target: '[[self-prediction-training]]'
  target_id: method:self-prediction-training
  confidence: high
- type: related_to
  target: '[[mean-absolute-deviation-calibration-error]]'
  target_id: metric:mean-absolute-deviation-calibration-error
  confidence: high
---

For the reported Llama-70B animal-sequence condition, self-prediction training
reduced mean absolute deviation from 23.0 to 8.7, while cross-prediction reached
21.3. Effects varied by behavior property and were less consistent for Llama
than for GPT-4o.
