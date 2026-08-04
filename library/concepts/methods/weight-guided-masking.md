---
aliases:
- WeMask
- weight-guided dimension masking
tags:
- kg/method
- concept
- method
kg:
  id: method:weight-guided-masking
  type: method
  status: canonical
area: methods
related:
- '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
- '[[massive-emergence-layer]]'
- '[[massive-activations]]'
- '[[attention-sink]]'
relationships:
- type: proposed_by
  target: '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
  target_id: paper:2605.08504
  confidence: high
- type: related_to
  target: '[[massive-emergence-layer]]'
  target_id: term:massive-emergence-layer
  confidence: high
- type: related_to
  target: '[[massive-activations]]'
  target_id: term:massive-activations
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: medium
---

Weight-guided masking (WeMask) selectively masks a top-weighted subset of the
massive-activation token's dimensions, identified from the ME Layer's weight
parameters, in order to relax the directional rigidity that massive
activations impose on that token's hidden state. It can be applied either as a
training-free inference-time intervention or incorporated into fine-tuning
(SFT, DPO, GRPO). Masking a partial fraction of the top-weighted dimensions
improves downstream performance and moderately attenuates attention sinks, but
masking all of them catastrophically degrades performance, indicating the
method's benefit comes from relaxing rather than eliminating the massive
activation.

**Why it matters here:** WeMask is a concrete, mechanistically-motivated
intervention on massive activations that improves instruction-following,
math-reasoning, and safety-alignment behavior without full retraining, making
it a template for targeted epistemic-relevant interventions on rigid,
input-invariant representations.

**Lineage:** proposed by
[[2605.08504--single-layer-explain-them-all-understanding-massive]], acting on
the token identified at the [[massive-emergence-layer]] where
[[massive-activations]] and their associated [[attention-sink]] originate.
