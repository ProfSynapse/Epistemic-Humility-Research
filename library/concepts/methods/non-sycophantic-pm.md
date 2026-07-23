---
aliases:
- non-sycophantic PM
- prompt-conditioned non-sycophantic PM
- truthfulness-prefixed PM
tags:
- kg/method
- concept
- method
kg:
  id: method:non-sycophantic-pm
  type: method
  status: canonical
area: methods
related:
- '[[2310.13548--towards-understanding-sycophancy]]'
- '[[reward-model]]'
- '[[best-of-n-sampling]]'
- '[[sycophancy]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[sycophancy-type-differential-rl-amplification]]'
relationships:
- type: proposed_by
  target: '[[2310.13548--towards-understanding-sycophancy]]'
  target_id: paper:2310.13548
  confidence: high
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[sycophancy-type-differential-rl-amplification]]'
  target_id: mechanism:sycophancy-type-differential-rl-amplification
  confidence: medium
---

A method for constructing a less sycophantic reward signal by prefixing the standard PM's prompt with a user request to provide truthful, belief-independent responses and an assistant acknowledgment. No additional training is required: the same PM weights are reused under a modified context, so the procedure applies at evaluation time only.

**Why it matters here:** Demonstrates that PM-level reward shaping (rather than base-policy retraining) can halve sycophantic response rates on the hardest misconceptions at N=4096. Provides a direct comparison point for locked training-regimen arms: a KTO or DPO arm changes the training loss, whereas this method changes the inference-time reward signal.

**Lineage:** Built on top of the Claude 2 PM (Anthropic, 2023) using Constitutional AI-style prompt conditioning (Bai et al., 2022b). Proposed in §4.2 of Sharma et al. (2023).
