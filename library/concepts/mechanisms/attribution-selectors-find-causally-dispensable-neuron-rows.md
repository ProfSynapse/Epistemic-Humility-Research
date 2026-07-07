---
aliases:
- attribution selectors identify dispensable neuron rows
- attribution row selectors pass LeRF audits
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:attribution-selectors-find-causally-dispensable-neuron-rows
  type: mechanism
  status: canonical
cause: "Attribution methods such as [[attnlrp-neuron-selector]], [[integrated-gradients]], and [[consensus-2-neuron-selector]] score neuron rows by contribution to the target objective"
effect: "Least-relevant rows can be masked with substantially lower language-modeling damage than rows chosen by magnitude, activation, or random baselines"
polarity: positive
area: mechanistic-interpretability
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[attnlrp-neuron-selector]]'
- '[[integrated-gradients]]'
- '[[consensus-2-neuron-selector]]'
- '[[neuron-row-masking]]'
relationships:
- type: supported_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
  evidence:
  - Table 5
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
  target: '[[neuron-row-masking]]'
  target_id: method:neuron-row-masking
  confidence: high
---

Attribution selectors can be causally faithful at the row level: when rows ranked least relevant by LRP, IG, or Consensus-2 are masked first, language-modeling damage stays far lower than for non-attribution baselines across several model families. The result supports using attribution selectors as candidates for mechanistic search, but only after direct causal validation.

**Implication:** Attribution should be treated as a hypothesis generator whose outputs are then audited by row masking, not as a standalone explanation.
