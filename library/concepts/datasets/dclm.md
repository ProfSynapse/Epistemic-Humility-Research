---
aliases:
- DCLM
- DataComp-LM
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:dclm
  type: dataset
  status: canonical
area: datasets
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
relationships:
- type: used_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
---

DCLM (DataComp-LM) is a large filtered web-text corpus built via a
model-based quality filtering pipeline over Common Crawl, used as a
pretraining and controlled-ablation training source for language models.

**Why it matters here:** Sun et al. train their ablation variants (normalization
configuration, attention gating, short-context-only loss) on DCLM, giving a
fixed, high-quality pretraining distribution across which spike magnitude, sink
ratio, and perplexity are compared.

**Lineage:** no formal derivation edges recorded in this vault yet.
