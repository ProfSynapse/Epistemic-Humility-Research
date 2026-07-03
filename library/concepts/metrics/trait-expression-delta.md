---
aliases:
- Δτ
- steering delta
- steered-minus-baseline trait score
- Trait-Expression Delta
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:trait-expression-delta
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
- '[[pretraining-checkpoint-tracing]]'
relationships:
- type: proposed_by
  target: '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
  target_id: paper:2605.13329
  confidence: high
- type: required_by
  target: '[[pretraining-checkpoint-tracing]]'
  target_id: method:pretraining-checkpoint-tracing
---

Trait-Expression Delta (delta-tau) quantifies steering effectiveness as the difference between the trait score under persona-vector steering and the unsteered baseline: delta_tau(M, M_r) = tau_steered(M, v^{M_r}) minus tau_base(M), where M is the target model, M_r is the source checkpoint supplying the persona vector, and tau is an LLM-judge-elicited trait score on a 0-100 scale. The metric supports both same-checkpoint and cross-checkpoint transfer evaluations, making it the primary instrument for measuring how well representations from one training stage steer behavior at another.

**Why it matters here:** Applied to epistemic traits such as confidence or hedging, delta-tau would measure whether a known-unknown probe extracted at checkpoint A causally installs abstention behavior at checkpoint B, which is a direct test of the training-free readout hypothesis.

**Lineage:** introduced in [[2605.13329--tracing-persona-vectors-through-llm-pretraining]]; consumed by [[pretraining-checkpoint-tracing]].
