---
aliases:
- KL-based temperature scaling
- pretrained-prior TS
tags:
- kg/method
- concept
- method
kg:
  id: method:pretrained-distribution-temperature-scaling
  type: method
  status: canonical
area: methods
related:
- '[[2310.11732--calibration-aligned-multiple-choice]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
- '[[direct-preference-optimization]]'
- '[[supervised-finetuning]]'
- '[[kl-divergence-penalty]]'
relationships:
- type: proposed_by
  target: '[[2310.11732--calibration-aligned-multiple-choice]]'
  target_id: paper:2310.11732
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
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
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: medium
---

A post-hoc calibration method that learns a single temperature parameter T per task by minimizing the KL divergence between the aligned model's scaled predictive distribution and the corresponding pretrained model's predictive distribution (Equation 6), using only five held-out examples per task. The intuition is that the pretrained model is well-calibrated under ICL, so recovering the aligned model's distribution relative to it is more sample-efficient than fitting a calibrator directly to accuracy.

**Why it matters here:** The only post-hoc method in the paper that outperforms out-of-the-box calibration on all tested tasks for Llama-2-Chat 70B with a five-example calibration set; applicable whenever the pretrained counterpart of an aligned model is accessible.

**Lineage:** Proposed in He et al. 2023 (arXiv:2310.11732) §5.2 as an extension of temperature scaling (Guo et al. 2017) with a KL-divergence objective.
