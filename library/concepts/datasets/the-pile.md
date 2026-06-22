---
aliases:
- Pile dataset
- EleutherAI Pile
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:the-pile
  type: dataset
  status: canonical
area: language-modeling
related:
- '[[tc2023--towards-monosemanticity]]'
relationships:
- type: related_to
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
---

The Pile is a large-scale, diverse English-language text corpus assembled by EleutherAI for training language models. It aggregates text from 22 sources spanning code, prose, scientific literature, web text, and multilingual content. In the sparse autoencoder interpretability work that relied on it, a one-layer transformer was trained on The Pile and the autoencoder was subsequently trained on 8 billion token-level activation samples drawn from the same corpus, providing broad domain coverage for discovering and evaluating learned features.

**Why it matters here:** Training and evaluation corpora shape the factual associations and uncertainty profiles that models develop, so knowing which corpus underlies a studied model is essential for interpreting calibration and abstention findings in context.

**Lineage:** produced by EleutherAI as an open pretraining resource; used as the activation source in [[tc2023--towards-monosemanticity]].
