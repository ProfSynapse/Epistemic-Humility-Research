---
aliases:
- cross-model uncertainty estimation
- general-purpose correctness estimation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:calibration-tuning-generalizes-across-models
  type: mechanism
  status: canonical
cause: "Fine-tuning a model on graded correctness data via calibration tuning (LoRA + Prompt)"
effect: "The resulting calibration tuner can estimate the uncertainty of a different model's generations more accurately than that target model estimates its own uncertainty, achieving higher AUROC when applied cross-model than the target model achieves via self-estimation"
polarity: enables
related:
- '[[2406.08391--taught-to-know-what-they-dont-know]]'
- '[[calibration-tuning]]'
- '[[diverse-training-enables-universal-probe-generalization]]'
- '[[pretrained-latent-representations-enable-calibration-generalization]]'
- '[[p-ik-ood-generalization-gap]]'
- '[[self-knowledge]]'
relationships:
- type: supported_by
  target: '[[2406.08391--taught-to-know-what-they-dont-know]]'
  target_id: paper:2406.08391
  confidence: high
- type: related_to
  target: '[[calibration-tuning]]'
  target_id: method:calibration-tuning
  confidence: high
- type: related_to
  target: '[[diverse-training-enables-universal-probe-generalization]]'
  target_id: mechanism:diverse-training-enables-universal-probe-generalization
  confidence: high
- type: related_to
  target: '[[pretrained-latent-representations-enable-calibration-generalization]]'
  target_id: mechanism:pretrained-latent-representations-enable-calibration-generalization
  confidence: high
- type: related_to
  target: '[[p-ik-ood-generalization-gap]]'
  target_id: mechanism:p-ik-ood-generalization-gap
  confidence: high
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: high
---

Kapoor et al. (2024) find that a Mistral 7B calibration tuner applied to LLaMA-2 7B generations achieves better AUROC for LLaMA-2 7B uncertainty than LLaMA-2 7B achieves when estimating its own correctness (Section 6.1, Figure 5 Center). The paper interprets this as evidence that calibration-tuned models learn a general-purpose correctness-estimation capability rather than a narrow self-knowledge signal about their own representations. The paper does not state that Mistral was trained specifically on LLaMA-2 7B outputs; it describes cross-model application of a Mistral calibration tuner to LLaMA-2 generations.
