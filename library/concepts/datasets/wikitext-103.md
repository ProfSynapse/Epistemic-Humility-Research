---
aliases:
- WikiText103
- wikitext103
- WikiText-103
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:wikitext-103
  type: dataset
  status: canonical
area: mechanistic-interpretability
related:
- '[[layer-depth-pattern-hierarchy]]'
relationships:
- type: related_to
  target: '[[layer-depth-pattern-hierarchy]]'
  target_id: term:layer-depth-pattern-hierarchy
---

A large-scale language modeling benchmark derived from Wikipedia featured articles, comprising over 100 million tokens of clean, verified prose across thousands of articles. It is commonly used to train and evaluate autoregressive language models at moderate scale. In the Geva et al. (2020) key-value memory study, the 16-layer transformer (Baevski and Auli 2019) that serves as the primary experimental subject was trained on this corpus, and the corpus's factual diversity directly shapes the range of patterns captured by the model's feed-forward keys.

**Why it matters here:** The Wikipedia source ensures that feed-forward keys can encode a broad range of factual associations, making the dataset a suitable substrate for studying where and how factual knowledge is stored in transformer layers.

**Lineage:** used as training corpus for experiments in [[layer-depth-pattern-hierarchy]]; a prerequisite dataset for the key-value memory analyses in the feed-forward interpretability literature.
