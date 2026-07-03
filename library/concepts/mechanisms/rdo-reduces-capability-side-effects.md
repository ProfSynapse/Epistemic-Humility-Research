---
aliases:
- Gradient-based RDO reduces capability side effects vs DIM
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rdo-reduces-capability-side-effects
  type: mechanism
  status: canonical
cause: "Optimising a [[refusal-direction-optimization]] direction with an explicit retain loss (KL penalty on safe-prompt behaviour) rather than using [[directional-ablation]] (DIM)"
effect: "TruthfulQA score degradation is reduced by ~40% on average compared to DIM directional ablation, while maintaining competitive jailbreak attack success rate"
polarity: decreases
related:
- '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
- '[[refusal-direction-optimization]]'
- '[[directional-ablation]]'
- '[[truthfulqa]]'
relationships:
- type: supported_by
  target: '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
  target_id: paper:2502.17420
  confidence: high
- type: related_to
  target: '[[refusal-direction-optimization]]'
  target_id: method:refusal-direction-optimization
- type: related_to
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
---

Difference-in-means directional ablation removes refusal by subtracting a single estimated direction from all layer activations, but it inevitably removes components that also carry safety-relevant and capability-relevant information. Adding an explicit retain loss (KL divergence between the modified and original model on safe prompts) during the gradient-based optimisation of the ablation direction confines the intervention to a direction that minimally disrupts benign behaviour. The concept-cones paper (arXiv:2502.17420) reports that this retain-constrained optimisation (RDO) cuts TruthfulQA degradation by approximately 40% relative to DIM while preserving competitive jailbreak attack success rates.
