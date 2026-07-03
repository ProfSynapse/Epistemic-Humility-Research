---
aliases:
- FineWeb
- FineWeb 10B tokens
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:fineweb-10bt
  type: dataset
  status: canonical
area: pretraining-data
related: []
relationships: []
---

A large-scale curated web text dataset (Penedo et al., 2024) derived from Common
Crawl with quality filtering to remove low-quality and duplicated content. The
MetaSAE paper uses the 10B-token slice, streamed with context length 128, for SAE
training (100M tokens) and co-occurrence evaluation (35M fresh tokens) on GPT-2
large residual stream activations. The strict train/eval token split ensures that
[[phi-coefficient-cooccurrence]] measurements are not contaminated by training
examples.

**Why it matters here:** As the pretraining corpus on which SAE feature atomicity
is evaluated, the composition of this data determines which co-occurrence patterns
are structural (model-internal) versus corpus-induced, a distinction that matters
whenever probes of internal epistemic states are built on activation data from
web-trained models.

**Lineage:** standalone dataset; used for SAE training and evaluation in the
[[metasae]] paper.
