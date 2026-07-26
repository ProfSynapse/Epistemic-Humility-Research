---
aliases:
- C4
- Colossal Clean Crawled Corpus
- C4 Corpus
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:c4-corpus
  type: dataset
  status: canonical
area: datasets
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
relationships:
- type: used_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
---

C4 (Colossal Clean Crawled Corpus) is a large filtered web-text corpus derived
from Common Crawl, introduced for T5 pretraining and widely reused as a generic
English text source for both training and activation-collection experiments.

**Why it matters here:** Stolfo et al. draw the 25,600-token evaluation sample
used for the entropy-neuron total-effect/direct-effect causal mediation
comparison from C4, giving a fixed natural-text distribution over which
LayerNorm-mediated effects are measured.

**Lineage:** no formal derivation edges recorded in this vault yet.
