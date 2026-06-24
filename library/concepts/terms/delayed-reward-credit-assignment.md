---
aliases:
- credit assignment in delayed-reward RL
- CoT delayed reward problem
- terminal-reward credit assignment
tags:
- kg/term
- concept
- term
kg:
  id: term:delayed-reward-credit-assignment
  type: term
  status: canonical
area: terms
related:
- '[[2606.06475--stepwise-trace-scoring]]'
- '[[rredcot]]'
- '[[mc-sampling-credit-assignment]]'
- '[[group-relative-policy-optimization]]'
- '[[policy-entropy-collapse]]'
- '[[reward-redistribution-reduces-grpo-variance]]'
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
  target: '[[mc-sampling-credit-assignment]]'
  target_id: method:mc-sampling-credit-assignment
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[policy-entropy-collapse]]'
  target_id: term:policy-entropy-collapse
  confidence: medium
- type: related_to
  target: '[[reward-redistribution-reduces-grpo-variance]]'
  target_id: mechanism:reward-redistribution-reduces-grpo-variance
  confidence: medium
---

The problem of attributing a terminal scalar reward backward to the intermediate steps or decisions that caused it, which is acute in CoT RL fine-tuning because the reward is only available after the full trace is complete and the trace may be thousands of tokens long.

**Why it matters here:** The core structural challenge motivating reward redistribution in CoT RL; high-variance gradient estimates from terminal-only reward slow convergence and may reinforce entire traces rather than the steps within them that matter.

**Lineage:** Classical RL credit assignment problem (Sutton and Barto); in LLM context made acute by the long-horizon nature of CoT generation and the absence of intermediate verifiers.
