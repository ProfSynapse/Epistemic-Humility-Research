---
aliases:
- Post-block steering
- Post-block activation adapter
tags:
- kg/method
- concept
- method
kg:
  id: method:post-block-activation-steering
  type: method
  status: canonical
area: methods
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[activation-steering]]'
- '[[representation-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[representation-finetuning]]'
  target_id: method:representation-finetuning
  confidence: high
---

Post-block activation steering places a trainable low-rank bottleneck adapter
after a transformer block's attention, MLP, and residual pathways. The adapter
is applied at every layer in the reported implementation.

**Why it matters here:** The method provides a learned activation-control
surface that can approach full fine-tuning performance with a small trainable
parameter budget.

**Lineage:** It is a form of [[activation-steering]] and differs from ReFT by
intervening on the full post-block residual output.
