---
aliases:
- concept cone
- multi-dimensional refusal cone
- RCO
- Refusal Cone Optimization
tags:
- kg/term
- concept
- term
kg:
  id: term:refusal-concept-cone
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
- '[[refusal-direction-optimization]]'
- '[[safety-residual-space]]'
- '[[dominant-refusal-direction]]'
relationships:
- type: proposed_by
  target: '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
  target_id: paper:2502.17420
  confidence: high
- type: derived_from
  target: '[[refusal-direction-optimization]]'
  target_id: method:refusal-direction-optimization
---

A refusal concept cone is a multi-dimensional polyhedral cone in LLM activation space spanned by an orthonormal basis such that every direction within the cone mediates refusal: ablating any basis direction removes refusal on harmful prompts, and adding any basis direction triggers refusal on harmless prompts. The construct extends the earlier single-direction picture of refusal to a subspace-level account, with cones of up to dimension five identified across tested model families.

**Why it matters here:** If refusal occupies a cone rather than a single direction, ablation or steering attacks that remove only one direction can be compensated by the remaining cone directions, directly relevant to the safety-residual-space question of how many independent actuators govern cautious or epistemically humble behavior, and whether the same multi-actuator geometry applies to abstention.

**Lineage:** derives from [[refusal-direction-optimization]]; described in [[2502.17420--geometry-refusal-large-language-models-concept-cones]]; related to [[safety-residual-space]] and [[dominant-refusal-direction]].
