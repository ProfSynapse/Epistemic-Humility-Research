---
aliases:
- Expand, Route, Ablate
- ERA
tags:
- kg/method
- concept
- method
kg:
  id: method:expand-route-ablate
  type: method
  status: canonical
area: unlearning
related:
- '[[gradient-routing]]'
- '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
relationships:
- type: proposed_by
  target: '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
  target_id: paper:2410.04332
  confidence: high
- type: derived_from
  target: '[[gradient-routing]]'
  target_id: method:gradient-routing
  confidence: high
---

Expand, Route, Ablate adds neurons to target layers, routes selected training gradients toward those dimensions, then deletes the added neurons. A short retain-set repair phase reduces general damage after ablation.
