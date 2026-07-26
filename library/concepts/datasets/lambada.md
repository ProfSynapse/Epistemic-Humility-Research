---
aliases:
- LAMBADA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:lambada
  type: dataset
  status: canonical
area: datasets
related:
- '[[2407.09298--transformer-layers-as-painters]]'
relationships:
- type: evaluation_set_for
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
---

LAMBADA is a word-prediction benchmark built from narrative passages where
the final word is predictable only by a human reader who has processed the
full passage's broader context, not from the local sentence alone. It tests
whether a language model has integrated long-range discourse context rather
than relying on short-range statistics.

**Why it matters here:** Used as one of the frozen-model evaluation
benchmarks in arXiv:2407.09298's layer-skipping and layer-reordering
experiments on Llama2 and BERT-Large.

**Lineage:** a widely adopted long-context language-modeling benchmark; no
direct lineage to other atoms in this vault.
