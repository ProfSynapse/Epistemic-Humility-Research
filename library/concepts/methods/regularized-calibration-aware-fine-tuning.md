---
aliases:
- RCFT
- Regularized CFT
- EM-regularized calibration fine-tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:regularized-calibration-aware-fine-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2505.01997--restoring-calibration-aligned-llms]]'
- '[[calibration-aware-fine-tuning]]'
- '[[supervised-finetuning]]'
- '[[expected-calibration-error]]'
- '[[calibration]]'
- '[[direct-preference-optimization]]'
relationships:
- type: proposed_by
  target: '[[2505.01997--restoring-calibration-aligned-llms]]'
  target_id: paper:2505.01997
  confidence: high
- type: related_to
  target: '[[calibration-aware-fine-tuning]]'
  target_id: method:calibration-aware-fine-tuning
  confidence: medium
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
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
---

An extension of CFT that adds an EM-algorithm-based ECE regularisation term (lambda=1) to the SFT loss for models in the non-calibratable regime. The E-step stratifies samples into confidence bins using the current model's max confidence; the M-step estimates a per-bin accuracy target and updates the model toward it. RCFT trades some calibration quality for substantially higher accuracy compared to plain CFT.

**Why it matters here:** RCFT is the appropriate tool when domain-specific fine-tuning pushes a model into the non-calibratable regime (accuracy above the critical threshold), where zero ECE is structurally unachievable. It reaches high accuracy (e.g., OLMo2-7B 0.851 vs DPO baseline 0.621) while keeping ECE competitive with temperature scaling.

**Lineage:** Proposed in arXiv:2505.01997 as Algorithm 1. Extends calibration-aware-fine-tuning with an EM loop. The EM framework draws on classical expectation-maximisation for latent-variable models applied to calibration bins.
