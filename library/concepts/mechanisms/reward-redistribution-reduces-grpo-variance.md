---
aliases:
- segment-level credit assignment reduces RL gradient variance
- RREDCoT variance reduction over terminal-reward GRPO
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reward-redistribution-reduces-grpo-variance
  type: mechanism
  status: canonical
cause: "Redistributing the terminal reward across CoT segments weighted by importance-sampling estimates of their contribution to the correct outcome, replacing the single-step terminal signal used in standard GRPO"
effect: "Gradient updates to the policy are shaped by segment-level signal rather than trace-level signal, reducing effective variance in the policy gradient and producing accuracy gains on hard math reasoning benchmarks in four of five test sets over vanilla GRPO"
polarity: decreases
related:
- '[[2606.06475--stepwise-trace-scoring]]'
- '[[rredcot]]'
- '[[group-relative-policy-optimization]]'
- '[[delayed-reward-credit-assignment]]'
- '[[importance-sampling-underestimates-cot-value]]'
- '[[mc-sampling-credit-assignment]]'
- '[[gradient-structure-encodes-output-correctness]]'
relationships:
- type: supported_by
  target: '[[2606.06475--stepwise-trace-scoring]]'
  target_id: paper:2606.06475
  confidence: high
- type: related_to
  target: '[[rredcot]]'
  target_id: method:rredcot
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[delayed-reward-credit-assignment]]'
  target_id: term:delayed-reward-credit-assignment
  confidence: high
- type: related_to
  target: '[[importance-sampling-underestimates-cot-value]]'
  target_id: mechanism:importance-sampling-underestimates-cot-value
  confidence: high
- type: related_to
  target: '[[mc-sampling-credit-assignment]]'
  target_id: method:mc-sampling-credit-assignment
  confidence: high
- type: related_to
  target: '[[gradient-structure-encodes-output-correctness]]'
  target_id: mechanism:gradient-structure-encodes-output-correctness
  confidence: high
---

Standard GRPO assigns the same scalar reward to every token in a trace, which corresponds to Monte Carlo return estimation with horizon equal to the full trace length. RREDCoT re-weights the per-segment gradient contribution by an IS-estimated advantage score, giving more weight to segments that are predictive of a correct terminal answer. On Qwen3-4B with a 25k-token budget, this produces AIME24 accuracy of 0.908 vs GRPO 0.850, AIME26 0.475 vs 0.442, Minerva 0.935 vs 0.915, and MATH500 0.823 vs 0.804. AIME25 is the exception (RREDCoT 0.583, GRPO 0.600). The mechanism comes at a 1.5-2x compute premium over vanilla GRPO (Section 5 Limitations) but is far cheaper than MC sampling-based credit assignment.
