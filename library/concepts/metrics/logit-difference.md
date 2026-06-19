---
aliases:
- logit difference
- logit diff
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:logit-difference
  type: metric
  status: canonical
area: metrics
related:
- '[[2309.16042--towards-best-practices-of-activation-patching-in-language-models]]'
- '[[activation-patching]]'
relationships:
- type: measured_by
  target: '[[2309.16042--towards-best-practices-of-activation-patching-in-language-models]]'
  target_id: paper:2309.16042
  confidence: high
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: medium
---

Logit difference measures the gap between selected output logits, often used as
a causal-patching or mechanistic-interpretability outcome.

