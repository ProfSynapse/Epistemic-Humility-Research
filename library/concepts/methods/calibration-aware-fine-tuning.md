---
aliases:
- CFT
- Calibration-Aware Fine-Tuning
- calibration fine-tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:calibration-aware-fine-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2505.01997--restoring-calibration-aligned-llms]]'
- '[[supervised-finetuning]]'
- '[[expected-calibration-error]]'
- '[[calibration]]'
- '[[overconfidence]]'
- '[[direct-preference-optimization]]'
- '[[regularized-calibration-aware-fine-tuning]]'
relationships:
- type: proposed_by
  target: '[[2505.01997--restoring-calibration-aligned-llms]]'
  target_id: paper:2505.01997
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[regularized-calibration-aware-fine-tuning]]'
  target_id: method:regularized-calibration-aware-fine-tuning
  confidence: medium
---

A supervised fine-tuning procedure applied to preference-aligned LLMs to restore calibration. CFT minimises a domain-specific SFT loss (cross-entropy on correct answers or a combined answer-plus-context loss) without an explicit ECE regularisation term, targeting models in the calibratable regime where zero ECE is achievable without accuracy loss. Implemented with QLoRA in the paper (rank=128, 5 epochs, 3,000 samples from MMLU, MedMCQA, OpenBookQA).

**Why it matters here:** CFT reduces conf-ECE by 68-88% across four aligned 7-8B models while preserving or improving accuracy and win rate, outperforming temperature scaling on all capability metrics. It is a concrete, reproducible recipe for recalibrating a DPO-aligned model before deployment.

**Lineage:** Proposed in arXiv:2505.01997. Applies standard supervised-finetuning loss; the theoretical justification draws on the calibratable/non-calibratable regime partition. Companion to regularized-calibration-aware-fine-tuning (RCFT) for the non-calibratable case.
