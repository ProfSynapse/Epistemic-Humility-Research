---
aliases:
- non-positive bias of IS segment estimator
- conservative IS bias in reward redistribution
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:importance-sampling-underestimates-cot-value
  type: mechanism
  status: canonical
cause: "Using an importance-sampling estimator that samples completions from the current policy to approximate segment-level state values in CoT RL, where the proposal distribution cannot cover all non-zero-probability, non-zero-utility completion sequences"
effect: "The estimator has a provable non-positive bias, systematically underestimating segment value rather than overestimating it, producing conservative credit assignment that avoids reinforcing spurious reasoning paths"
polarity: decreases
related:
- '[[2606.06475--stepwise-trace-scoring]]'
- '[[rredcot]]'
- '[[mc-sampling-credit-assignment]]'
- '[[delayed-reward-credit-assignment]]'
- '[[group-relative-policy-optimization]]'
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
  target: '[[mc-sampling-credit-assignment]]'
  target_id: method:mc-sampling-credit-assignment
  confidence: high
- type: related_to
  target: '[[delayed-reward-credit-assignment]]'
  target_id: term:delayed-reward-credit-assignment
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
---

Equation 10 in the paper and the derivation in Appendix C.5 show that the IS estimator's expected value is always at or below the true segment value when utilities are non-negative. The bias is zero only when the proposal distribution q covers the entirety of Y, U (the set of all sequences with non-zero utility). In practice the proposal cannot cover this set, so the estimator is conservative. This property makes over-reinforcing an incorrect but fluent CoT segment less likely than under-reinforcing a genuinely helpful one, which the authors treat as the safer failure mode for training.
