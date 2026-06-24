---
aliases:
- ToF
- turn of flip
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:turn-of-flip
  type: metric
  status: canonical
area: metrics
related:
- '[[2505.23840--sycon-bench]]'
- '[[number-of-flip]]'
- '[[sycophancy]]'
- '[[sycon-bench]]'
relationships:
- type: proposed_by
  target: '[[2505.23840--sycon-bench]]'
  target_id: paper:2505.23840
  confidence: high
- type: related_to
  target: '[[number-of-flip]]'
  target_id: metric:number-of-flip
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

The mean earliest dialogue turn at which a model's response diverges from its expected (principled) stance, averaged over benchmark instances. Higher ToF indicates greater resistance to conversational pressure.

**Why it matters here:** Captures how quickly a model capitulates under sustained user disagreement, a dimension of sycophancy not measurable from single-turn assessments.

**Lineage:** Introduced in SYCON Bench (2505.23840) alongside Number-of-Flip to provide complementary early-flip vs. oscillation views.
