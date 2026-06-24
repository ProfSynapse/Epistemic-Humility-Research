---
aliases:
- VS
- effective number of modes
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:vendi-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2604.16027--posttraining-diversity-collapse]]'
- '[[output-diversity-collapse]]'
- '[[self-consistency]]'
- '[[decoding-randomness]]'
relationships:
- type: proposed_by
  target: '[[2604.16027--posttraining-diversity-collapse]]'
  target_id: paper:2604.16027
  confidence: high
- type: related_to
  target: '[[output-diversity-collapse]]'
  target_id: term:output-diversity-collapse
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: medium
---

A diversity metric that measures the effective number of dissimilar outputs via the eigenvalue entropy of a similarity kernel. Given K outputs with similarity matrix G (trace-normalized), Vendi Score = exp(-sum lambda_i * log lambda_i). VS=1 when all outputs are identical; VS=K when all outputs are orthogonal. Typically computed over the SBERT cosine similarity kernel.

**Why it matters here:** Provides an interpretable 'effective number of modes' framing that SBERT pairwise distance alone does not. A model with VS=1.3 on GSM8K produces 16 outputs with effectively one distinct mode, making additional samples useless for majority voting.

**Lineage:** Proposed by Friedman et al. (2023). Applied by Karouzos et al. (2604.16027) to trace output diversity collapse across OLMo 3 post-training stages.
