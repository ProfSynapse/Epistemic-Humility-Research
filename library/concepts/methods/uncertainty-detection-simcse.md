---
aliases:
- uncertainty detection method
- reference-sentence similarity scoring
- SimCSE-based Uncertainty Detection
tags:
- kg/method
- concept
- method
kg:
  id: method:uncertainty-detection-simcse
  type: method
  status: canonical
area: methods
related:
- '[[2305.18153--selfaware-know-what-they-dont-know]]'
- '[[self-knowledge-f1]]'
relationships:
- type: proposed_by
  target: '[[2305.18153--selfaware-know-what-they-dont-know]]'
  target_id: paper:2305.18153
  confidence: high
- type: required_by
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
---

Uncertainty-Detection-SimCSE is an automated method for determining whether a model response expresses epistemic uncertainty. It computes cosine similarity between candidate response sentences (via a sliding window) and a curated set of reference sentences with uncertain meaning, using a SimCSE encoder. A response is classified as uncertainty-expressing when any window exceeds a cosine similarity threshold of 0.75 against the reference set.

**Why it matters here:** This method is the evaluation backbone for the SelfAware dataset: it allows automatic scoring of whether model outputs appropriately hedge on unanswerable questions, providing the "expressed uncertainty" half of the [[self-knowledge-f1]] metric without requiring human annotation of each response.

**Lineage:** prerequisite of [[self-knowledge-f1]]; introduced by [[2305.18153--selfaware-know-what-they-dont-know]].
