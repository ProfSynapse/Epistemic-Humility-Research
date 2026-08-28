---
aliases:
- Conditional Activation Steering
- CAST
tags:
- kg/method
- concept
- method
kg:
  id: method:conditional-activation-steering
  type: method
  status: canonical
area: methods
related:
- '[[2409.05907--programming-refusal-conditional-activation-steering]]'
- '[[activation-steering]]'
- '[[condition-vector]]'
relationships:
- type: proposed_by
  target: '[[2409.05907--programming-refusal-conditional-activation-steering]]'
  target_id: paper:2409.05907
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[condition-vector]]'
  target_id: term:condition-vector
  confidence: high
---

Conditional Activation Steering applies a behavior vector only when a hidden-state similarity score crosses a threshold defined by a condition vector. It can combine several conditions with logical rules and can invert a condition to act on its complement.

**Why it matters here:** CAST provides a concrete runtime architecture in which one internal readout decides whether another internal intervention changes generation.

**Lineage:** It extends activation steering with a separate condition-vector sensor and threshold rule.
