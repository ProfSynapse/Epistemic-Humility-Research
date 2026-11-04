---
aliases:
- Weight-Space Programming
- reasoning-guided direct weight editing
tags:
- kg/method
- concept
- method
kg:
  id: method:weight-space-programming
  type: method
  status: canonical
related:
- '[[web-20261102--sparks-weight-space-programming]]'
- '[[rank-one-model-editing]]'
- '[[activation-steering]]'
relationships:
- type: proposed_by
  target: '[[web-20261102--sparks-weight-space-programming]]'
  target_id: paper:web-20261102-weight-space-programming
  confidence: high
- type: related_to
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

A general-purpose LLM reasons about neural tensors and directly writes weight
changes under a task specification. In the large-model demonstration, the editor
uses a persistent CPU kernel and a limited forward-query tool; gradient training
and iterative fitting to a loss are prohibited.

This includes an agent's diagnosis and choice of program. A predetermined rank-one
sweep tests a particular edit family, rather than reproducing that discovery loop.
