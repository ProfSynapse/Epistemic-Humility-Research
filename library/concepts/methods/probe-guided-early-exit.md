---
aliases:
- probe-based early exit
- confidence-based early exit
- adaptive early exit
- Probe-Guided Early Exit
tags:
- kg/method
- concept
- method
kg:
  id: method:probe-guided-early-exit
  type: method
  status: canonical
area: efficiency
related:
- '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
- '[[attention-probing]]'
relationships:
- type: proposed_by
  target: '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
  target_id: paper:2603.05488
  confidence: high
- type: derived_from
  target: '[[attention-probing]]'
  target_id: method:attention-probing
---

Probe-guided early exit uses the confidence of an attention probe trained on
intermediate hidden-state activations as a stopping signal during generation:
once the probe's confidence in a predicted answer exceeds a threshold, token
generation is halted and the probe's answer is returned in place of the remainder
of the chain-of-thought. The strategy exploits the finding that models often
commit internally to an answer long before their emitted tokens acknowledge that
commitment, making further token generation computationally wasteful.

**Why it matters here:** The method converts the faithfulness gap (internal
commitment earlier than emitted commitment) into a practical efficiency gain, and
simultaneously raises the question of whether the suppressed reasoning tokens
were genuinely deliberative or merely performative.

**Lineage:** derives from [[attention-probing]] as the probe machinery; proposed
in [[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]],
which introduced the reasoning-theater framing that motivates the early-exit
design.
