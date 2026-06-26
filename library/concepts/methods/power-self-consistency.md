---
aliases:
- PSC
- power SC
- Power Self-Consistency
tags:
- kg/method
- concept
- method
kg:
  id: method:power-self-consistency
  type: method
  status: canonical
area: methods
related:
- '[[2606.27359--when-likely-answers-right-sequence-probability-correctness]]'
- '[[self-consistency]]'
relationships:
- type: proposed_by
  target: '[[2606.27359--when-likely-answers-right-sequence-probability-correctness]]'
  target_id: paper:2606.27359
  confidence: high
- type: variation_of
  target: '[[self-consistency]]'
  target_id: method:self-consistency
---

Power Self-Consistency draws samples from the power distribution (sequences generated via power-SMC, which amplifies token-level probabilities) and aggregates them by majority vote. It extends [[self-consistency]] to decoding-aware sampling, motivated by evidence that power-SMC samples can outperform standard low-temperature samples in downstream accuracy. Aggregation follows the same majority-vote logic as ordinary self-consistency but operates over a distribution that up-weights high-probability token paths, coupling the sample selection step to the confidence signal rather than treating it as independent.

**Why it matters here:** PSC demonstrates that the choice of sampling distribution interacts with how sequence probability tracks correctness, which bears directly on whether internal probability signals can reliably guide self-improvement without external verification.

**Lineage:** variation of [[self-consistency]]; proposed in [[2606.27359--when-likely-answers-right-sequence-probability-correctness]].
