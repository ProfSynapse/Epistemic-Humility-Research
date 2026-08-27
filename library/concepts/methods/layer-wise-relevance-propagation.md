---
aliases:
- LRP
- layerwise relevance propagation
- Layer-wise Relevance Propagation
tags:
- kg/method
- concept
- method
kg:
  id: method:layer-wise-relevance-propagation
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[projection-layer-wise-relevance-propagation]]'
- '[[attnlrp-neuron-selector]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: related_to
  target: '[[projection-layer-wise-relevance-propagation]]'
  target_id: method:projection-layer-wise-relevance-propagation
  confidence: high
- type: related_to
  target: '[[attnlrp-neuron-selector]]'
  target_id: method:attnlrp-neuron-selector
  confidence: high
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

Layer-wise Relevance Propagation is an attribution method that redistributes a model output score backward through the network to assign relevance to intermediate components or input features. In transformer interpretability it can be adapted to attention and MLP structures to rank model components by contribution to a target scalar, such as next-token loss or a refusal/compliance logit margin.

**Why it matters here:** LRP provides a gradient-based selector whose causal validity can be tested by row masking. In the refusal audit, LRP-derived row rankings often outperform activation and magnitude baselines, but the paper treats this as an empirical result rather than as guaranteed faithfulness.

**Lineage:** general attribution family; [[projection-layer-wise-relevance-propagation]] is a projection-specific variant, and [[attnlrp-neuron-selector]] is the transformer-row selector variant used in the refusal audit.
