---
aliases:
- SelfAware dataset
- SA
- SelfAware benchmark
- SAW
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:selfaware
  type: dataset
  status: canonical
area: datasets
related:
- '[[2305.18153--selfaware-know-what-they-dont-know]]'
relationships:
- type: proposed_by
  target: '[[2305.18153--selfaware-know-what-they-dont-know]]'
  target_id: paper:2305.18153
  confidence: high
---

SelfAware is a dataset of 1,032 unanswerable questions spanning five categories
(No Scientific Consensus, Imagination, Completely Subjective, Too Many Variables,
and Philosophical), paired with 2,337 answerable counterparts drawn from similar
topics. Introduced by Yin et al. (2023), it is designed to measure whether LLMs
can distinguish questions that have no definite answer from those that do.

**Why it matters here:** SelfAware is a standard out-of-domain evaluation target
for self-knowledge studies; models trained on abstention tasks (including
R-Tuning and related SFT/DPO/KTO regimes) are tested on it to assess
generalization beyond the training distribution.

**Lineage:** a standalone self-knowledge benchmark; proposed in
[[2305.18153--selfaware-know-what-they-dont-know]].
