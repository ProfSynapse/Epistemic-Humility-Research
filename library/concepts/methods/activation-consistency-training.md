---
aliases:
- Activation Consistency Training
- ACT
tags:
- kg/method
- concept
- method
kg:
  id: method:activation-consistency-training
  type: method
  status: canonical
area: representation-training
related:
- '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
- '[[activation-patching]]'
relationships:
- type: proposed_by
  target: '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
  target_id: paper:2510.27062
  confidence: high
- type: derived_from
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: high
---

Activation Consistency Training minimizes squared residual-stream distance between a wrapped prompt and a stop-gradient clean-prompt target. The paper applies the objective across all layers at the longest token suffix shared by the prompt pair.

**Why it matters here:** ACT changes model weights using an internal-state objective, but the target is a paired prompt state rather than an answerability signal.
