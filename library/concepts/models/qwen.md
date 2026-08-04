---
aliases:
- Qwen
- Qwen (1.5 series)
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
relationships:
- type: used_by
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
---

Qwen is Alibaba's open-weight decoder-only language model family. This atom
covers the pre-Qwen3 generation of Qwen checkpoints used as a general open-
weight model family; distinct from the newer [[qwen3]], [[qwen3-32b]], and
[[qwen2-5-7b-instruct]] atoms, which cover specific later-generation
checkpoints.

**Why it matters here:** One of the seven open-weight model families layer-
pruned in arXiv:2403.17887; notable there for having the smallest robust-
pruning threshold (~20%) of the models tested, making it the family most
sensitive to depth removal.

**Lineage:** no formal derivation edges recorded in this vault yet.
