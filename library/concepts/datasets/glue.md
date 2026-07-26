---
aliases:
- GLUE
- General Language Understanding Evaluation
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:glue
  type: dataset
  status: canonical
area: datasets
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[superglue]]'
relationships:
- type: evaluation_set_for
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: high
- type: related_to
  target: '[[superglue]]'
  target_id: dataset:superglue
---

GLUE is a suite of nine sentence- and sentence-pair-level natural-language-
understanding tasks (including textual entailment, sentiment, and semantic
similarity) used as a single aggregate benchmark for evaluating and comparing
general-purpose language representations.

**Why it matters here:** Used as a BERT-Large evaluation benchmark in
arXiv:2407.09298's layer-skipping, layer-reordering, and parallel-execution
experiments, standing in for the encoder-style task family the way ARC/GSM8K/
HellaSwag/WinoGrande stand in for the decoder-style (Llama2) task family.

**Lineage:** predecessor to the harder [[superglue]] suite; no direct
lineage to other atoms in this vault.
