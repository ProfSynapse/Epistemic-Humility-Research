---
aliases:
- prefix conditioned sampling
- PCS
- step-conditioned continuation sampling
tags:
- kg/method
- concept
- method
kg:
  id: method:prefix-conditioned-sampling
  type: method
  status: canonical
area: methods
related:
- '[[2606.03969--faithful-calibration-framework]]'
- '[[cmfg-star]]'
- '[[faithful-calibration]]'
- '[[self-consistency]]'
- '[[consistency-based-confidence]]'
- '[[p-true]]'
relationships:
- type: proposed_by
  target: '[[2606.03969--faithful-calibration-framework]]'
  target_id: paper:2606.03969
  confidence: high
- type: related_to
  target: '[[cmfg-star]]'
  target_id: metric:cmfg-star
  confidence: medium
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
  confidence: medium
---

An inference-time method for estimating intrinsic confidence at each step of a reasoning trace by sampling k continuations conditioned on each step-prefix rather than on the full trace. Uses k=10 continuations of up to 200 tokens per step, subsampling at most 20 steps per trace while always retaining the first and last step. The resulting distribution over continuations approximates the model's local uncertainty at each reasoning step while controlling for the conditional dependencies that accumulate across a long chain-of-thought.

**Why it matters here:** Addresses the core technical challenge of measuring intrinsic confidence in long chain-of-thought outputs, where strong autoregressive dependencies between steps make end-of-trace token probabilities a poor proxy for genuine uncertainty. Directly applicable to any Phase 1 or mechanism program evaluation that reads confidence off Qwen3 CoT outputs.

**Lineage:** Introduced in Gani et al. 2026 (arXiv:2606.03969) to support their faithful calibration framework for large reasoning models.
