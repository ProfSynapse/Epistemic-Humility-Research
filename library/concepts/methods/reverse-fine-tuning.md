---
aliases:
- reverse fine-tuning
- reFT
tags:
- kg/method
- concept
- method
kg:
  id: method:reverse-fine-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2311.12786--mechanistically-analyzing-effects-fine-tuning-procedurally-defined]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2311.12786--mechanistically-analyzing-effects-fine-tuning-procedurally-defined]]'
  target_id: paper:2311.12786
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
---

Reverse fine-tuning continues training a fine-tuned model on examples sampled from its original pretraining distribution. The method tests how quickly a behavior associated with a pretraining capability returns.

**Why it matters here:** Fast restoration can distinguish behavioral suppression from learning a capability anew, although it does not by itself identify the retained computation.
