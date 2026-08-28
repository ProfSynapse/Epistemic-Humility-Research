---
aliases:
- mechanistic supervision
- supervision of learned mechanisms
tags:
- kg/term
- concept
- term
kg:
  id: term:mechanistic-supervision
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

Mechanistic supervision is the use of data to direct which internal network regions learn selected computations. It constrains training internals in addition to specifying an input-output objective.
