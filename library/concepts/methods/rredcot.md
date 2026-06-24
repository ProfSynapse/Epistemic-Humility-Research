---
aliases:
- Reward REDistribution for Chain of Thoughts
- segment-level reward redistribution for CoT RL
tags:
- kg/method
- concept
- method
kg:
  id: method:rredcot
  type: method
  status: canonical
area: methods
related:
- '[[2606.06475--stepwise-trace-scoring]]'
- '[[group-relative-policy-optimization]]'
- '[[delayed-reward-credit-assignment]]'
- '[[mc-sampling-credit-assignment]]'
- '[[importance-sampling-underestimates-cot-value]]'
- '[[reward-redistribution-reduces-grpo-variance]]'
relationships:
- type: proposed_by
  target: '[[2606.06475--stepwise-trace-scoring]]'
  target_id: paper:2606.06475
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[delayed-reward-credit-assignment]]'
  target_id: term:delayed-reward-credit-assignment
  confidence: medium
- type: related_to
  target: '[[mc-sampling-credit-assignment]]'
  target_id: method:mc-sampling-credit-assignment
  confidence: medium
- type: related_to
  target: '[[importance-sampling-underestimates-cot-value]]'
  target_id: mechanism:importance-sampling-underestimates-cot-value
  confidence: medium
- type: related_to
  target: '[[reward-redistribution-reduces-grpo-variance]]'
  target_id: mechanism:reward-redistribution-reduces-grpo-variance
  confidence: medium
---

A reward redistribution method for GRPO-style RL fine-tuning of reasoning models that segments CoT traces and uses an importance-sampling estimator built from the model's own log-probabilities to assign credit to each segment without additional generation, following the RUDDER lineage of return decomposition.

**Why it matters here:** Provides segment-level training signal within long reasoning chains without the 100+ GPU-hour cost of Monte Carlo value estimation, enabling more fine-grained RL credit assignment for math reasoning models.

**Lineage:** Extends RUDDER (Arjona-Medina et al. 2019) by replacing the RUDDER LSTM with the language model itself as the value estimator; builds on GRPO (DeepSeekMath 2024) as the base optimization algorithm.
