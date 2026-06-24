---
aliases:
- CT
- correctness-supervised fine-tuning
- graded-dataset calibration fine-tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:calibration-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2406.08391--taught-to-know-what-they-dont-know]]'
- '[[low-rank-adaptation]]'
- '[[supervised-finetuning]]'
- '[[linear-probe]]'
- '[[verbalized-confidence]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[mmlu]]'
- '[[kl-divergence-penalty]]'
- '[[calibration-aware-fine-tuning]]'
- '[[p-true]]'
relationships:
- type: proposed_by
  target: '[[2406.08391--taught-to-know-what-they-dont-know]]'
  target_id: paper:2406.08391
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: medium
- type: related_to
  target: '[[calibration-aware-fine-tuning]]'
  target_id: method:calibration-aware-fine-tuning
  confidence: medium
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
  confidence: medium
---

A supervised fine-tuning procedure that trains a language model on a small labeled dataset of correct and incorrect model-generated answers to predict the probability that a given answer is correct. Kapoor et al. (2024) implement this with LoRA adapters (rank r=8, alpha=32, dropout 0.1, 8-bit quantization) plus a JSD regularizer to keep the fine-tuned model close to the base, and frame correctness prediction as a binary token-choice problem (LoRA + Prompt parameterization). Approximately 20,000 examples from 16 benchmark datasets are used for training.

**Why it matters here:** Provides a parameter-efficient, data-efficient recipe for attaching reliable uncertainty estimates to any open-source LLM with minimal compute cost and no access to closed-model internals. Shows that 1000 labeled examples suffice to outperform all prompting and sampling baselines on open-ended MMLU, and that the resulting estimator generalizes across subject-matter shifts, format shifts, and even cross-model application.

**Lineage:** Proposed in arXiv:2406.08391. Builds on the correctness-prediction framing of Lin et al. and Kadavath et al. Related to calibration-aware-fine-tuning (CFT, arXiv:2505.01997) which targets preference-aligned models; calibration tuning targets base and instruction-tuned models using a graded correctness dataset rather than an ECE loss.
