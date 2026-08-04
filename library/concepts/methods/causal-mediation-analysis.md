---
aliases:
- Causal Mediation Analysis
- total effect vs direct effect
tags:
- kg/method
- concept
- method
kg:
  id: method:causal-mediation-analysis
  type: method
  status: canonical
area: methods
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[layer-normalization]]'
relationships:
- type: used_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[layer-normalization]]'
  target_id: term:layer-normalization
  confidence: medium
---

Causal mediation analysis decomposes a component's total effect on a model's
output into a direct effect (holding a hypothesized mediator fixed) and the
remaining effect that passes through the mediator, letting a researcher test
whether an intermediate computation actually carries the causal influence.

**Why it matters here:** Stolfo et al. apply this framework to entropy neurons,
comparing each neuron's total effect (TE) on the loss/output entropy against
its direct effect (DE) with the final LayerNorm's normalization scale held
constant. A large TE-DE gap for entropy neurons but not random neurons is the
evidence that their effect is mediated by [[layer-normalization]] rather than
by directly shifting logits.

**Lineage:** no formal derivation edges recorded in this vault yet.
