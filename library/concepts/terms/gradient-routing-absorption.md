---
aliases:
- gradient routing absorption
- absorption effect
tags:
- kg/term
- concept
- term
kg:
  id: term:gradient-routing-absorption
  type: term
  status: canonical
area: terminology
related:
- '[[gradient-routing]]'
- '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
relationships:
- type: proposed_by
  target: '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
  target_id: paper:2410.04332
  confidence: high
- type: related_to
  target: '[[gradient-routing]]'
  target_id: method:gradient-routing
  confidence: high
---

Gradient-routing absorption is the paper's proposed effect in which routing a narrow labeled subset creates features useful for a broader related task. Those features then reduce error on unrouted related data and reduce pressure to learn duplicates elsewhere.
