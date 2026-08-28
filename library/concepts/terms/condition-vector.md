---
aliases:
- Condition Vector
- conditional steering vector
tags:
- kg/term
- concept
- term
kg:
  id: term:condition-vector
  type: term
  status: canonical
area: terms
related:
- '[[2409.05907--programming-refusal-conditional-activation-steering]]'
- '[[steering-vector]]'
relationships:
- type: proposed_by
  target: '[[2409.05907--programming-refusal-conditional-activation-steering]]'
  target_id: paper:2409.05907
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

A condition vector is a layer-specific direction extracted from contrastive prompt classes. CAST uses similarity between the current hidden state and this direction to decide whether to apply a separate behavior vector.

**Why it matters here:** It is the sensor half of a hidden-state-gated actuator.

**Lineage:** It adapts contrastive steering-vector extraction for context detection rather than direct behavior modification.
