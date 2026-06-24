---
aliases:
- Elicitation-Then-Calibration
- EliCal
- two-stage honesty alignment
tags:
- kg/method
- concept
- method
kg:
  id: method:elical
  type: method
  status: canonical
area: methods
related:
- '[[2510.17509--elical-universal-honesty-alignment]]'
- '[[consistency-based-confidence]]'
- '[[confidence-elicitation]]'
- '[[low-rank-adaptation]]'
- '[[self-consistency]]'
- '[[auroc]]'
- '[[expected-calibration-error]]'
- '[[pretrained-latent-representations-enable-calibration-generalization]]'
relationships:
- type: proposed_by
  target: '[[2510.17509--elical-universal-honesty-alignment]]'
  target_id: paper:2510.17509
  confidence: high
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[confidence-elicitation]]'
  target_id: method:confidence-elicitation
  confidence: medium
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[pretrained-latent-representations-enable-calibration-generalization]]'
  target_id: mechanism:pretrained-latent-representations-enable-calibration-generalization
  confidence: medium
---

A two-stage annotation-efficient framework for LLM honesty alignment. Stage 1 (Confidence Elicitation) trains a frozen-backbone LoRA plus linear confidence head to predict self-consistency confidence using large-scale, label-free supervision. Stage 2 (Confidence Calibration) fine-tunes the same head on a small set of correctness-labeled examples. The head maps the final-layer hidden state of the last question token to a scalar confidence score via MSE loss.

**Why it matters here:** Achieves roughly 98% of full-supervision AUROC with only 1,000 correctness labels (0.18% of the full HonestyBench training set), and generalizes better than calibration-only approaches to out-of-distribution task formats (MMLU), because the elicitation stage encodes consistency signals rather than domain-specific labels.

**Lineage:** Two-stage design parallels pre-training/fine-tuning: the elicitation stage is an inexpensive pretraining on self-consistency, and calibration is a low-cost fine-tuning on correctness. Related to consistency-based-confidence (its Stage 1 supervision source), low-rank-adaptation (its adapter architecture), and confidence-elicitation (the broader category).
