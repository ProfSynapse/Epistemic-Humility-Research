---
aliases:
- SAE Feature Ablation Enables Compliance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sae-feature-ablation-enables-compliance
  type: mechanism
  status: canonical
cause: "Ablating the minimal set of causal [[sparse-autoencoder|SAE features]] aligned with the [[refusal-direction]], identified via [[sae-causal-feature-discovery]]"
effect: "Model flips from refusal to compliance on harmful prompts (ASR 0.33 for Gemma, 0.70 for LLaMA after two-stage feature identification)"
polarity: enables
related:
- '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
- '[[sparse-autoencoder]]'
- '[[refusal-direction]]'
- '[[sae-causal-feature-discovery]]'
relationships:
- type: supported_by
  target: '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
  target_id: paper:2509.09708
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
- type: related_to
  target: '[[sae-causal-feature-discovery]]'
  target_id: method:sae-causal-feature-discovery
---

By first identifying which SAE features co-activate with the refusal direction using correlation, then pruning to only those whose ablation causally reduces refusal (Stage 2), a minimal feature set sufficient to jailbreak the model can be isolated. Ablating this minimal set on the C-PRO task corpus achieves attack success rates of 0.33 on Gemma and 0.70 on LLaMA without modifying any model weights (arXiv:2509.09708). The mechanism confirms that refusal is partially mediated by a sparse, identifiable set of SAE features rather than being distributed uniformly across all model computations.
