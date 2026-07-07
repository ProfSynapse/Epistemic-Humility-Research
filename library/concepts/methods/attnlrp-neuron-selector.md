---
aliases:
- AttnLRP selector
- LRP neuron selector
- attention LRP neuron selector
tags:
- kg/method
- concept
- method
kg:
  id: method:attnlrp-neuron-selector
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[layer-wise-relevance-propagation]]'
- '[[neuron-selector-causal-audit]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: derived_from
  target: '[[layer-wise-relevance-propagation]]'
  target_id: method:layer-wise-relevance-propagation
  confidence: high
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
- type: related_to
  target: '[[neuron-selector-causal-audit]]'
  target_id: method:neuron-selector-causal-audit
  confidence: high
---

The AttnLRP neuron selector adapts Layer-wise Relevance Propagation to transformer rows, scoring attention and MLP projection rows by their relevance to a target objective. In the Faithfulness to Refusal audit, it is one of the attribution selectors compared against random, magnitude, Wanda, and activation baselines.

**Why it matters here:** AttnLRP is an example of a selector that can look mechanistically grounded yet still requires direct causal testing. Its success in row-masking audits makes it a useful candidate for future epistemic-humility component searches, provided specificity and utility controls are retained.

**Lineage:** derives from [[layer-wise-relevance-propagation]] and is evaluated by [[neuron-selector-causal-audit]] in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
