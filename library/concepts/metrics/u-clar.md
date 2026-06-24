---
aliases:
- U-Clar
- correct clarification rate
- U-Clar_c
- conditional correct-clarification rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:u-clar
  type: metric
  status: canonical
area: metrics
related:
- '[[2604.17073--abstain-r1]]'
- '[[abstain-test]]'
- '[[abstention-rate]]'
- '[[abstain-accuracy]]'
- '[[clarification-aware-rlvr-reward]]'
- '[[unanswerable-questions]]'
relationships:
- type: proposed_by
  target: '[[2604.17073--abstain-r1]]'
  target_id: paper:2604.17073
  confidence: high
- type: related_to
  target: '[[abstain-test]]'
  target_id: dataset:abstain-test
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
- type: related_to
  target: '[[abstain-accuracy]]'
  target_id: metric:abstain-accuracy
  confidence: medium
- type: related_to
  target: '[[clarification-aware-rlvr-reward]]'
  target_id: method:clarification-aware-rlvr-reward
  confidence: medium
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: medium
---

A metric on unanswerable queries measuring the fraction of unanswerable questions for which a model both outputs an explicit abstention (boxed 'I don't know') and provides a post-refusal clarification judged semantically correct by a verifier against a reference clarification. U-Clar_c conditions on the subset where the model chose to refuse.

**Why it matters here:** Separates models that refuse from models that refuse usefully; existing abstention metrics such as abstention-rate capture only the refusal decision (U-Ref) and miss the quality of post-refusal clarification, underestimating training success for clarification-capable models.

**Lineage:** Introduced alongside abstain-test; complements abstention-rate (U-Ref) and abstain-accuracy; verification during training uses xVerify-3B-Ia and offline evaluation uses o4-mini.
