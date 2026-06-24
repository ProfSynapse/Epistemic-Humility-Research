---
aliases:
- AED
- accuracy engagement distance
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:accuracy-engagement-distance
  type: metric
  status: canonical
area: metrics
related:
- '[[2410.17234--semantic-entropy-abstention]]'
- '[[abstention-rate]]'
- '[[abstain-accuracy]]'
- '[[over-abstention]]'
- '[[hallucination]]'
relationships:
- type: proposed_by
  target: '[[2410.17234--semantic-entropy-abstention]]'
  target_id: paper:2410.17234
  confidence: high
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
- type: related_to
  target: '[[abstain-accuracy]]'
  target_id: metric:abstain-accuracy
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
---

A normalized Euclidean distance metric for abstention fine-tuning evaluation. A fine-tuned model is represented as a point (I, C) in the space of incorrect and correct answers over a dataset of size |D|. AED is the normalized distance from that point to the ideal model at (0, |D|): sqrt((I^2 + (|D| - C)^2) / (2 * |D|^2)). Ranges from 0 (ideal) to 1. Penalizes both hallucinations (high I) and over-abstention (low C), unlike accuracy-only metrics that ignore engagement.

**Why it matters here:** Resolves the accuracy-only metric's blind spot: a model that abstains from nearly every question can match a useful model on accuracy while being far worse on helpfulness. AED provides a single scalar that captures the hallucination-over-abstention tradeoff, making it directly compatible with the effects.csv evaluation schema for Phase 1 arms.

**Lineage:** Proposed by Tjandra et al. (arXiv:2410.17234, 2024), adapting Tian et al. (2023) biography-truthfulness comparison to the abstention-evaluation setting.
