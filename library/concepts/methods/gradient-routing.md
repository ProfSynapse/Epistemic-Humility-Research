---
aliases:
- Gradient Routing
- gradient masking by data point
tags:
- kg/method
- concept
- method
kg:
  id: method:gradient-routing
  type: method
  status: canonical
area: training
related:
- '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
- '[[mechanistic-supervision]]'
relationships:
- type: proposed_by
  target: '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
  target_id: paper:2410.04332
  confidence: high
- type: related_to
  target: '[[mechanistic-supervision]]'
  target_id: term:mechanistic-supervision
  confidence: high
---

Gradient routing applies user-specified, data-dependent weights to selected gradient paths during backpropagation. Standard backpropagation is recovered when all route weights equal one, and the forward pass is unchanged.

**Why it matters here:** The method lets a training process constrain which parameters or activation dimensions learn from selected examples.
