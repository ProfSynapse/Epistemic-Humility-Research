---
aliases:
- Monte Carlo intermediate value estimation
- MC sampling for CoT segment values
tags:
- kg/method
- concept
- method
kg:
  id: method:mc-sampling-credit-assignment
  type: method
  status: canonical
area: methods
related:
- '[[2606.06475--stepwise-trace-scoring]]'
- '[[rredcot]]'
- '[[group-relative-policy-optimization]]'
- '[[delayed-reward-credit-assignment]]'
- '[[importance-sampling-underestimates-cot-value]]'
relationships:
- type: proposed_by
  target: '[[2606.06475--stepwise-trace-scoring]]'
  target_id: paper:2606.06475
  confidence: high
- type: related_to
  target: '[[rredcot]]'
  target_id: method:rredcot
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[delayed-reward-credit-assignment]]'
  target_id: term:delayed-reward-credit-assignment
  confidence: medium
- type: related_to
  target: '[[importance-sampling-underestimates-cot-value]]'
  target_id: mechanism:importance-sampling-underestimates-cot-value
  confidence: medium
---

The use of Monte Carlo rollouts from each intermediate state in a CoT trace to estimate segment-level state values for reward redistribution in RL fine-tuning; provides an unbiased but computationally expensive value signal.

**Why it matters here:** Establishes the theoretical gold standard for segment-level value estimation in CoT RL, but its cost (100 GPU-hours for 30 problems) makes it impractical for on-policy training, motivating cheaper approximations like RREDCoT.

**Lineage:** Standard MC return estimation from RL applied to the token/segment level inside CoT fine-tuning; conceptually prior to RUDDER and RREDCoT.
