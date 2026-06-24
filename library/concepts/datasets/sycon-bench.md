---
aliases:
- SYcophantic CONformity Bench
- SYCON
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:sycon-bench
  type: dataset
  status: canonical
area: datasets
related:
- '[[2505.23840--sycon-bench]]'
- '[[sycophancy]]'
- '[[turn-of-flip]]'
- '[[number-of-flip]]'
- '[[false-premise-questions]]'
relationships:
- type: proposed_by
  target: '[[2505.23840--sycon-bench]]'
  target_id: paper:2505.23840
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[turn-of-flip]]'
  target_id: metric:turn-of-flip
  confidence: medium
- type: related_to
  target: '[[number-of-flip]]'
  target_id: metric:number-of-flip
  confidence: medium
- type: related_to
  target: '[[false-premise-questions]]'
  target_id: term:false-premise-questions
  confidence: medium
---

A multi-turn, free-form sycophancy evaluation benchmark consisting of 500 prompts across three scenarios: debate (100 topics), challenging unethical queries (200), and false presuppositions (200), each with five dialogue turns of escalating persuasive pressure judged by GPT-4o.

**Why it matters here:** First benchmark to quantify sycophancy in sustained multi-turn free-form dialogue at scale, enabling separate diagnosis of how quickly and how often models abandon correct stances under social pressure.

**Lineage:** Built from IBM Project Debater topics (debate), StereoSet (unethical queries), and CREPE (false presupposition); judging validated against human annotation at kappa 0.63-0.92 across scenarios.
