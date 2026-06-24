---
aliases:
- EAD
- expectation-adjusted distinct
- adjusted distinct N-grams
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:expectation-adjusted-distinct-ngrams
  type: metric
  status: canonical
area: metrics
related:
- '[[2310.06452--rlhf-generalisation-diversity]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
- '[[rlhf-rl-optimisation-collapses-per-input-diversity]]'
relationships:
- type: proposed_by
  target: '[[2310.06452--rlhf-generalisation-diversity]]'
  target_id: paper:2310.06452
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[rlhf-rl-optimisation-collapses-per-input-diversity]]'
  target_id: mechanism:rlhf-rl-optimisation-collapses-per-input-diversity
  confidence: medium
---

A syntactic output diversity metric that counts the number of distinct N-grams (averaged over N=1...) in a set of model outputs, with a bias-correction term that removes the tendency of longer outputs to score higher. Defined by Liu et al. (2022).

**Why it matters here:** EAD enables fair comparison of syntactic diversity across outputs of different lengths, which is critical when comparing SFT and RLHF models that differ in typical output length.

**Lineage:** Proposed in Liu et al. (2022, ACL); used as the primary syntactic diversity metric in Kirk et al. (2023) (arXiv 2310.06452).
