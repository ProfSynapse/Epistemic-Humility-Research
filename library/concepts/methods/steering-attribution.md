---
aliases:
- integrated steering attribution
- steering-effect feature attribution
tags:
- kg/method
- concept
- method
kg:
  id: method:steering-attribution
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2603.21396--mechanisms-introspective-awareness]]'
- '[[integrated-gradients]]'
- '[[sparse-feature-circuits]]'
- '[[activation-steering]]'
relationships:
- type: proposed_by
  target: '[[2603.21396--mechanisms-introspective-awareness]]'
  target_id: paper:2603.21396
  confidence: high
- type: derived_from
  target: '[[integrated-gradients]]'
  target_id: method:integrated-gradients
  confidence: high
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

Steering attribution decomposes the total effect of intervention strength on an
output target into feature contributions. It multiplies each feature's
sensitivity to steering by that feature's gradient influence on the target,
then integrates along the path from zero to the selected strength. Layer cuts
and feature-to-feature edge weights support attribution graphs from the injected
source to the output decision.

**Why it matters here:** A feature can respond strongly to steering without
affecting output, or affect output without responding to steering. Their product
selects features that satisfy both conditions.
