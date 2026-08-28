---
aliases:
- CBL
- concept bottleneck
- interpretable concept-neuron layer
tags:
- kg/term
- concept
- term
kg:
  id: term:concept-bottleneck-layer
  type: term
  status: canonical
area: terms
related:
- '[[2412.07992--concept-bottleneck-large-language-models]]'
- '[[openreview-L9U5MJJleF--concept-bottleneck-generative-models]]'
- '[[concept-bottleneck-large-language-model]]'
- '[[concept-bottleneck-generative-model]]'
relationships:
- type: proposed_by
  target: '[[2412.07992--concept-bottleneck-large-language-models]]'
  target_id: paper:2412.07992
  confidence: medium
- type: related_to
  target: '[[concept-bottleneck-large-language-model]]'
  target_id: method:concept-bottleneck-large-language-model
  confidence: high
- type: related_to
  target: '[[concept-bottleneck-generative-model]]'
  target_id: method:concept-bottleneck-generative-model
  confidence: high
---

A concept bottleneck layer contains neurons trained to represent named, human-interpretable concepts. A following linear layer exposes how each concept activation contributes to class or token logits and allows direct intervention on the concept values.

**Why it matters here:** It provides an architectural point where an internal readout can directly influence generation rather than remain a post-hoc diagnostic.

**Lineage:** CB-LLMs adapt this established concept-bottleneck structure to large text datasets and autoregressive language generation.
