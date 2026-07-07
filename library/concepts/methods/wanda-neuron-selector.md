---
aliases:
- Wanda selector
- WANDA row selector
- weight and activation neuron selector
tags:
- kg/method
- concept
- method
kg:
  id: method:wanda-neuron-selector
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[neuron-selector-causal-audit]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
- type: related_to
  target: '[[neuron-selector-causal-audit]]'
  target_id: method:neuron-selector-causal-audit
  confidence: high
---

Wanda is a weight-and-activation selector that scores a row using the absolute weight values scaled by activation root-mean-square statistics. It is often used as a pruning baseline because it is cheaper than full attribution while still including activation information.

**Why it matters here:** In the refusal causal audit, Wanda functions as a strong non-attribution baseline. Its failures on some LeRF/MoRF sweeps show that cheap weight/activation salience is not equivalent to causal faithfulness.

**Lineage:** evaluated as a selector baseline in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
