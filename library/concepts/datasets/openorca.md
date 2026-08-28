---
aliases:
- OpenOrca
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:openorca
  type: dataset
  status: canonical
area: datasets
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[supervised-finetuning]]'
relationships:
- type: used_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
---

OpenOrca is an instruction-following dataset of explanation traces and
responses. The paper uses a 262,144-example subset for full-parameter
supervised fine-tuning.

**Why it matters here:** Its small fraction of refusal completions provides
incidental pressure against an installed refusal-ablation edit.

**Lineage:** The dataset is used as a downstream instruction-tuning surface.
