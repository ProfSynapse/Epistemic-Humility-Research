---
aliases:
- refusal-with-clarification reward
- clarification-aware reward
- abstention clarification reward
tags:
- kg/method
- concept
- method
kg:
  id: method:clarification-aware-rlvr-reward
  type: method
  status: canonical
area: methods
related:
- '[[2604.17073--abstain-r1]]'
- '[[group-relative-policy-optimization]]'
- '[[ternary-reward-design]]'
- '[[rule-based-reward-model]]'
- '[[unanswerable-questions]]'
- '[[u-clar]]'
- '[[rlvr-post-training-degrades-abstention]]'
relationships:
- type: proposed_by
  target: '[[2604.17073--abstain-r1]]'
  target_id: paper:2604.17073
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[ternary-reward-design]]'
  target_id: method:ternary-reward-design
  confidence: medium
- type: related_to
  target: '[[rule-based-reward-model]]'
  target_id: method:rule-based-reward-model
  confidence: medium
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: medium
- type: related_to
  target: '[[u-clar]]'
  target_id: metric:u-clar
  confidence: medium
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: medium
---

A composite reward for GRPO training that combines (1) a format check, (2) a strict-correctness reward for answerable queries with a -1 under-abstention penalty for false refusal, and (3) a refusal-with-clarification reward that awards 0.3 for explicit abstention and an additional 0.7 when a verifier judges the post-refusal clarification semantically aligned with the reference missing-information description.

**Why it matters here:** Directly optimizes both when to abstain and what to say after abstaining, making clarification quality a first-class training target rather than an emergent property; the penalty coefficient controls an explicit abstention-accuracy tradeoff.

**Lineage:** Extends group-relative-policy-optimization with a structured unanswerable-query reward; verifier is xVerify-3B-Ia during training and o4-mini for offline evaluation; builds on ternary-reward-design and rule-based-reward-model patterns.
