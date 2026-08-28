---
aliases:
- Weight Vectors Monitoring
- behavioral drift monitoring with weight directions
- task-vector monitoring
tags:
- kg/method
- concept
- method
kg:
  id: method:weight-vector-monitoring
  type: method
  status: canonical
area: monitoring
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[contrastive-weight-steering]]'
- '[[cosine-similarity]]'
- '[[emergent-misalignment]]'
relationships:
- type: proposed_by
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: medium
- type: derived_from
  target: '[[contrastive-weight-steering]]'
  target_id: method:contrastive-weight-steering
  confidence: high
- type: related_to
  target: '[[cosine-similarity]]'
  target_id: metric:cosine-similarity
  confidence: high
- type: related_to
  target: '[[emergent-misalignment]]'
  target_id: term:emergent-misalignment
  confidence: high
---

Weight-vector monitoring compares a fine-tuning update with contrastive behavioral directions by cosine similarity. Fierro and Roger test whether updates from narrow bad-advice fine-tunes align more with an evil direction than good or control updates do.

**Why it matters here:** It is a weights-level monitoring proposal that may expose behavioral drift without first finding prompts that elicit the behavior. The paper treats the evidence as preliminary and does not establish operational precision.

**Lineage:** It reuses the directions produced by [[contrastive-weight-steering]] for monitoring instead of editing.
