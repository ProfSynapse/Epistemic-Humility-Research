---
aliases:
- BERT-Large
- Bidirectional Encoder Representations from Transformers
tags:
- kg/model
- concept
- model
kg:
  id: model:bert
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[2407.09298--transformer-layers-as-painters]]'
relationships:
- type: used_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
---

BERT is a bidirectional, encoder-only transformer pretrained with masked-
language-modeling and next-sentence-prediction objectives. BERT-Large (24
layers) is the larger of the two originally released sizes and is commonly
fine-tuned on downstream classification and understanding tasks such as
GLUE.

**Why it matters here:** BERT-Large is the encoder-architecture counterpart
to Llama2 in arXiv:2407.09298's layer-manipulation experiments, used to show
that the middle-layers-share-a-representation-space finding, and its
consequences for layer skipping, weight sharing, and reordering, hold across
both decoder-only and encoder-only transformer architectures.

**Lineage:** no formal derivation edges in this vault.
