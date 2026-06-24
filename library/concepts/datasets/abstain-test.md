---
aliases:
- AbstainTest
- Abstain Test benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:abstain-test
  type: dataset
  status: canonical
area: datasets
related:
- '[[2604.17073--abstain-r1]]'
- '[[abstentionbench]]'
- '[[selfaware]]'
- '[[u-clar]]'
- '[[abstain-r1]]'
- '[[clarification-aware-rlvr-reward]]'
relationships:
- type: proposed_by
  target: '[[2604.17073--abstain-r1]]'
  target_id: paper:2604.17073
  confidence: high
- type: related_to
  target: '[[abstentionbench]]'
  target_id: dataset:abstentionbench
  confidence: medium
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: medium
- type: related_to
  target: '[[u-clar]]'
  target_id: metric:u-clar
  confidence: medium
- type: related_to
  target: '[[abstain-r1]]'
  target_id: model:abstain-r1
  confidence: medium
- type: related_to
  target: '[[clarification-aware-rlvr-reward]]'
  target_id: method:clarification-aware-rlvr-reward
  confidence: medium
---

An evaluation benchmark of approximately 2.9K instances constructed from AbstentionBench task subsets plus the SUM test set, designed to measure both abstention and post-refusal clarification quality using six metrics: A-Acc, A-FU, A-Acc_c, U-Ref, U-Clar, and U-Clar_c.

**Why it matters here:** Provides the first systematic evaluation protocol that separates refusal rate from clarification quality on unanswerable queries, enabling training methods to be assessed on both when to abstain and whether the abstention is informative.

**Lineage:** Constructed from AbstentionBench subsets using the same generation pipeline as abstain-cot; extends coverage with the SUM test set; introduced alongside abstain-r1.
