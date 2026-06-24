---
aliases:
- elicitation-then-calibration mechanism
- pre-calibration self-consistency pretraining
- two-stage honesty learning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-consistency-elicitation-reduces-correctness-annotation-need
  type: mechanism
  status: canonical
cause: "Large-scale training on self-consistency confidence targets (Stage 1) that teaches the model to externalize its internal consistency signal before any correctness labels are introduced"
effect: "A subsequent Stage 2 calibration step requires far fewer correctness annotations to reach near-upper-bound AUROC discrimination, and generalizes better to out-of-distribution task formats than calibration-only training from scratch"
polarity: enables
related:
- '[[2510.17509--elical-universal-honesty-alignment]]'
- '[[elical]]'
- '[[consistency-based-confidence]]'
- '[[pretrained-latent-representations-enable-calibration-generalization]]'
- '[[confidence-elicitation]]'
- '[[low-rank-adaptation]]'
relationships:
- type: supported_by
  target: '[[2510.17509--elical-universal-honesty-alignment]]'
  target_id: paper:2510.17509
  confidence: high
- type: related_to
  target: '[[elical]]'
  target_id: method:elical
  confidence: high
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: high
- type: related_to
  target: '[[pretrained-latent-representations-enable-calibration-generalization]]'
  target_id: mechanism:pretrained-latent-representations-enable-calibration-generalization
  confidence: high
- type: related_to
  target: '[[confidence-elicitation]]'
  target_id: method:confidence-elicitation
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

When a LoRA-augmented confidence head is first trained on self-consistency supervision across a large question set, it encodes a consistency-correlated internal signal in the final-layer representation. This foundation means Stage 2 correctness calibration is not learning to express confidence from scratch but correcting an already-functional confidence estimator, reducing the annotation requirement by roughly three orders of magnitude (1k vs 560k labels) while preserving 98% of discriminative power. The generalization advantage on MMLU suggests the consistency signal is more transferable than domain-specific correctness labels, which can overfit to the question format seen during calibration.
