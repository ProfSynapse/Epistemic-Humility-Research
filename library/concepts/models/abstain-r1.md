---
aliases:
- Abstain-R1 3B
- abstain r1
tags:
- kg/model
- concept
- model
kg:
  id: model:abstain-r1
  type: model
  status: canonical
area: models
related:
- '[[2604.17073--abstain-r1]]'
- '[[group-relative-policy-optimization]]'
- '[[abstain-test]]'
- '[[abstain-cot]]'
- '[[clarification-aware-rlvr-reward]]'
- '[[rlvr-post-training-degrades-abstention]]'
- '[[unanswerable-questions]]'
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
  target: '[[abstain-test]]'
  target_id: dataset:abstain-test
  confidence: medium
- type: related_to
  target: '[[abstain-cot]]'
  target_id: dataset:abstain-cot
  confidence: medium
- type: related_to
  target: '[[clarification-aware-rlvr-reward]]'
  target_id: method:clarification-aware-rlvr-reward
  confidence: medium
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: medium
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: medium
---

A 3B language model fine-tuned from Qwen2.5-3B-Instruct via a two-stage pipeline (SFT cold-start on Abstain-CoT followed by GRPO with a clarification-aware RLVR reward) to simultaneously abstain on unanswerable queries and produce semantically correct post-refusal clarifications identifying the missing information.

**Why it matters here:** Demonstrates that calibrated abstention and post-refusal clarification can be acquired through targeted verifiable rewards at 3B scale, matching or exceeding much larger models on unanswerability metrics while preserving answerable-query performance.

**Lineage:** Built on Qwen2.5-3B-Instruct; trained with group-relative-policy-optimization; evaluated on abstain-test, abstain-qa, and selfaware.
