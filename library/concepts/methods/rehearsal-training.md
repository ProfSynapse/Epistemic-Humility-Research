---
aliases:
- rehearsal training
- knowledge flow probing via rehearsal
tags:
- kg/method
- concept
- method
kg:
  id: method:rehearsal-training
  type: method
  status: canonical
area: methods
related:
- '[[2410.06913--craft]]'
- '[[craft]]'
- '[[supervised-finetuning]]'
- '[[sft-abstention-causes-over-refusal]]'
- '[[sft-knowledge-state-shifts-during-training]]'
relationships:
- type: proposed_by
  target: '[[2410.06913--craft]]'
  target_id: paper:2410.06913
  confidence: high
- type: related_to
  target: '[[craft]]'
  target_id: method:craft
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[sft-abstention-causes-over-refusal]]'
  target_id: mechanism:sft-abstention-causes-over-refusal
  confidence: medium
- type: related_to
  target: '[[sft-knowledge-state-shifts-during-training]]'
  target_id: mechanism:sft-knowledge-state-shifts-during-training
  confidence: medium
---

A preliminary fine-tuning pass on a model using only its highest-certainty and highest-correctness samples, designed not to introduce new knowledge but to reveal how the model's knowledge state naturally evolves during SFT. The difference in knowledge state before and after rehearsal characterizes the knowledge flow, enabling detection and correction of dynamic conflicts in RAIT data.

**Why it matters here:** Rehearsal training is the mechanism by which CRaFT detects dynamic conflict: it shows that a substantial fraction of initially-unknown samples become answerable during training, exposing which IdK labels will produce contradictory supervision. The technique is a lightweight, reward-free data-curation tool layerable on any SFT pipeline.

**Lineage:** proposed in 2410.06913 as a component of craft; derives from supervised-finetuning
