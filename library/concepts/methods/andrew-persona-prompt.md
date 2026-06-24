---
aliases:
- Andrew prompt
- third-person persona prompting
- distanced self-talk prompting
tags:
- kg/method
- concept
- method
kg:
  id: method:andrew-persona-prompt
  type: method
  status: canonical
area: methods
related:
- '[[2505.23840--sycon-bench]]'
- '[[sycophancy]]'
- '[[sycon-bench]]'
- '[[turn-of-flip]]'
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
  target: '[[sycon-bench]]'
  target_id: dataset:sycon-bench
  confidence: medium
- type: related_to
  target: '[[turn-of-flip]]'
  target_id: metric:turn-of-flip
  confidence: medium
---

A system prompt that instructs the model to reason and respond as a named third-person character (Andrew) rather than as itself, inspired by distanced self-talk, used as a sycophancy-reduction strategy without any weight update.

**Why it matters here:** Reduces sycophancy by up to 63.8% in debate settings and outperforms an explicit anti-sycophancy instruction alone, providing a zero-cost inference-time mitigation.

**Lineage:** Inspired by Kross et al. (2014) distanced self-talk; evaluated in SYCON Bench (2505.23840) alongside Non-Sycophantic and Andrew+Non-Sycophantic prompts.
