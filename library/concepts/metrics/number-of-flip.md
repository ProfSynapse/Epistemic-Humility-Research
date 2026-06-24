---
aliases:
- NoF
- number of flip
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:number-of-flip
  type: metric
  status: canonical
area: metrics
related:
- '[[2505.23840--sycon-bench]]'
- '[[turn-of-flip]]'
- '[[sycophancy]]'
- '[[sycon-bench]]'
relationships:
- type: proposed_by
  target: '[[2505.23840--sycon-bench]]'
  target_id: paper:2505.23840
  confidence: high
- type: related_to
  target: '[[turn-of-flip]]'
  target_id: metric:turn-of-flip
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[sycon-bench]]'
  target_id: dataset:sycon-bench
  confidence: medium
---

The mean total number of times a model reverses its stance across all turns of a multi-turn dialogue, averaged over benchmark instances. Lower NoF indicates greater stance stability.

**Why it matters here:** Captures oscillation and inconsistency under sustained pressure, complementing Turn-of-Flip which measures only the first capitulation point.

**Lineage:** Introduced alongside ToF in SYCON Bench (2505.23840).
