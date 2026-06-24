---
aliases:
- Calibration Aware Token-level Training Objective
- calibration-aware DPO
- DPO+CATTO
tags:
- kg/method
- concept
- method
kg:
  id: method:catto
  type: method
  status: canonical
area: methods
related:
- '[[2601.23096--catto-per-token-calibration]]'
- '[[direct-preference-optimization]]'
- '[[regularized-calibration-aware-fine-tuning]]'
- '[[cdpo-calibrated-dpo]]'
- '[[calibration-aware-fine-tuning]]'
- '[[expected-calibration-error]]'
- '[[temperature-scaling]]'
- '[[calibration]]'
- '[[overconfidence]]'
- '[[confidence-at-k]]'
relationships:
- type: proposed_by
  target: '[[2601.23096--catto-per-token-calibration]]'
  target_id: paper:2601.23096
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[regularized-calibration-aware-fine-tuning]]'
  target_id: method:regularized-calibration-aware-fine-tuning
  confidence: medium
- type: related_to
  target: '[[cdpo-calibrated-dpo]]'
  target_id: method:cdpo-calibrated-dpo
  confidence: medium
- type: related_to
  target: '[[calibration-aware-fine-tuning]]'
  target_id: method:calibration-aware-fine-tuning
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
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
  target: '[[confidence-at-k]]'
  target_id: method:confidence-at-k
  confidence: medium
---

A calibration-aware preference optimization objective that augments DPO with a differentiable per-token L1 calibration loss. The loss uses a sigmoid of the ground-truth vs best-competitor probability margin as a smooth correctness surrogate and penalizes the absolute deviation between predicted confidence and this surrogate. Applied to both preferred and dispreferred sequences during training; introduces no extra model parameters and negligible overhead relative to DPO.

**Why it matters here:** Prevents confidence drift during preference alignment without requiring a separate calibration phase or additional compute. Directly applicable to Phase 1 DPO arm on Qwen3-4B. Provides calibrated token probabilities that enable Confidence@k inference-time selection.

**Lineage:** Proposed in arXiv:2601.23096. Builds on direct-preference-optimization by adding a per-token calibration term grounded in population L1 calibration risk and Jensen's inequality. Distinct from cdpo-calibrated-dpo (which uses verbalized confidence labels) and from regularized-calibration-aware-fine-tuning (which is a post-hoc supervised phase). Companion to confidence-at-k.
