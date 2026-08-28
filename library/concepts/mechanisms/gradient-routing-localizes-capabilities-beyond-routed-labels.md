---
aliases:
- Gradient routing localizes capabilities beyond routed labels
- Narrow routes absorb broader semantic features
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gradient-routing-localizes-capabilities-beyond-routed-labels
  type: mechanism
  status: canonical
cause: "Training gradients from a narrow labeled or token-defined subset are restricted to a designated network region."
effect: "The region acquires features useful for semantically related unrouted data, reducing duplicate learning elsewhere."
polarity: redistributes
related:
- '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
- '[[gradient-routing]]'
- '[[gradient-routing-absorption]]'
relationships:
- type: supported_by
  target: '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
  target_id: paper:2410.04332
  confidence: high
- type: related_to
  target: '[[gradient-routing]]'
  target_id: method:gradient-routing
  confidence: high
- type: related_to
  target: '[[gradient-routing-absorption]]'
  target_id: term:gradient-routing-absorption
  confidence: high
---

Evidence includes California-related vocabulary aligning to the routed residual coordinate, virology loss remaining elevated after routed-token exclusion, and localization under partial labeling. The causal account called absorption is proposed in the discussion rather than directly isolated from alternatives.
