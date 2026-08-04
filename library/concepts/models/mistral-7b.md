---
aliases:
- Mistral 7B
- Mistral-7B
tags:
- kg/model
- concept
- model
kg:
  id: model:mistral-7b
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[2407.09298--transformer-layers-as-painters]]'
relationships:
- type: used_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: medium
---

Mistral 7B is Mistral AI's open-weight 7-billion-parameter decoder-only
transformer, notable for grouped-query attention and sliding-window attention
that give it strong performance-per-parameter relative to contemporaneous
open models.

**Why it matters here:** Used as an additional decoder-only architecture in
arXiv:2407.09298 to help establish that the middle-layer representation-
sharing and skip-tolerance findings generalize beyond the Llama2 family.

**Lineage:** no formal derivation edges in this vault.
