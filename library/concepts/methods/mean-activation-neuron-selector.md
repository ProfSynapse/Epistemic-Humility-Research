---
aliases:
- MeanActivation selector
- mean activation selector
- activation magnitude selector
tags:
- kg/method
- concept
- method
kg:
  id: method:mean-activation-neuron-selector
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

MeanActivation is a neuron-row selector that ranks rows by the mean absolute output activation observed on a calibration set. Because it uses activation magnitude directly, it can produce highly stable rankings across batches.

**Why it matters here:** The Faithfulness to Refusal audit identifies MeanActivation as a cautionary example: a selector can be rank-stable yet causally unfaithful. That makes it a useful negative control for epistemic-humility component searches that might otherwise over-trust stable salience maps.

**Lineage:** evaluated as an activation baseline in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
