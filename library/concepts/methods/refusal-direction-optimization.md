---
aliases:
- RDO
- gradient-based refusal direction
- Refusal Direction Optimization (RDO)
tags:
- kg/method
- concept
- method
kg:
  id: method:refusal-direction-optimization
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
- '[[difference-in-means]]'
- '[[refusal-concept-cone]]'
relationships:
- type: proposed_by
  target: '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
  target_id: paper:2502.17420
  confidence: high
- type: derived_from
  target: '[[difference-in-means]]'
  target_id: method:difference-in-means
---

Refusal Direction Optimization is a gradient-based representation engineering method that learns a unit vector in activation space to mediate refusal. It combines three losses: a directional-ablation loss (projecting out the vector causes the model to answer harmful prompts), an activation-addition loss (adding the vector causes the model to refuse harmless prompts), and a KL-divergence retain loss that penalizes behavioral drift on safe inputs. The retain loss weight controls the trade-off between attack success rate and capability side effects.

**Why it matters here:** RDO demonstrates that a single learned direction can serve as a precise actuator for refusal behavior, raising the parallel question of whether analogous directions might steer epistemic-humility behaviors such as abstention or hedging with comparable precision and minimal collateral effect.

**Lineage:** extends [[difference-in-means]] by replacing the analytic mean-difference with gradient optimization; described in [[2502.17420--geometry-refusal-large-language-models-concept-cones]]; motivates [[refusal-concept-cone]] as a multi-dimensional generalization.
