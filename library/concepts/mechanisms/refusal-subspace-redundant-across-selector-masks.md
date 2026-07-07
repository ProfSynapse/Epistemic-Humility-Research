---
aliases:
- redundant refusal subspace
- disjoint refusal masks can install refusal
- refusal has multiple sufficient row sets
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:refusal-subspace-redundant-across-selector-masks
  type: mechanism
  status: canonical
cause: "Multiple attribution selectors identify largely disjoint neuron-row sets for refusal behavior"
effect: "Different row masks can nevertheless install similar refusal behavior, implying a redundant refusal subspace rather than a unique minimal mechanism"
polarity: explains
area: mechanistic-interpretability
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[attnlrp-neuron-selector]]'
- '[[integrated-gradients]]'
- '[[consensus-2-neuron-selector]]'
- '[[contrastive-refusal-mask]]'
relationships:
- type: supported_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
  evidence:
  - Section 6.5
- type: related_to
  target: '[[attnlrp-neuron-selector]]'
  target_id: method:attnlrp-neuron-selector
  confidence: high
- type: related_to
  target: '[[integrated-gradients]]'
  target_id: method:integrated-gradients
  confidence: high
- type: related_to
  target: '[[consensus-2-neuron-selector]]'
  target_id: method:consensus-2-neuron-selector
  confidence: high
- type: related_to
  target: '[[contrastive-refusal-mask]]'
  target_id: method:contrastive-refusal-mask
  confidence: high
---

Refusal can be represented redundantly across neuron rows. Faithfulness to Refusal reports low overlap between LRP and IG top-row sets even when both can install refusal, and harm-domain overlap clusters semantically similar domains such as hate and crime.

**Implication:** A discovered refusal mask should be interpreted as a sufficient implementation, not necessarily the unique mechanism. This matters for causal claims about whether a model's refusal is internally faithful or just one of several redundant control routes.
