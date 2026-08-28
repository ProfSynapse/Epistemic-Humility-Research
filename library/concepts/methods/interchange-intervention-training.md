---
aliases:
- Interchange Intervention Training
- IIT
tags:
- kg/method
- concept
- method
kg:
  id: method:interchange-intervention-training
  type: method
  status: canonical
area: methods
related:
- '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
- '[[causal-intervention]]'
- '[[causal-abstraction]]'
relationships:
- type: proposed_by
  target: '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
  target_id: paper:2112.00826
  confidence: high
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: high
- type: related_to
  target: '[[causal-abstraction]]'
  target_id: term:causal-abstraction
  confidence: high
---

Interchange intervention training aligns a high-level causal variable with a neural representation. It swaps that representation between source and base inputs, then trains the neural model to match the high-level model's counterfactual output.

**Why it matters here:** IIT provides a training objective for making behavior depend on a specified internal variable, which could be adapted to an answerability readout.

**Lineage:** The method extends interchange-intervention analysis from a post hoc test into a differentiable training objective.
