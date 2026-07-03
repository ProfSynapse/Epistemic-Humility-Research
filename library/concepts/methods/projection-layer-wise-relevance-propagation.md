---
aliases:
- PLRP
- projection LRP
- token-wise PLRP
- Projection-based Layer-wise Relevance Propagation (PLRP)
tags:
- kg/method
- concept
- method
kg:
  id: method:projection-layer-wise-relevance-propagation
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
- '[[trigger-removal-attack]]'
relationships:
- type: proposed_by
  target: '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
  target_id: paper:2502.09674
  confidence: high
- type: related_to
  target: '[[trigger-removal-attack]]'
  target_id: method:trigger-removal-attack
---

Projection-based Layer-wise Relevance Propagation extends the standard LRP attribution framework by projecting token-level relevance scores onto a chosen orthogonal direction in the model's residual stream rather than attributing to the scalar output logit. Applied to a target direction in the safety residual space, PLRP scores each input token by how much it activates that direction, producing an interpretable ranking of trigger tokens. Relevance is propagated backward through each transformer layer using standard LRP backpropagation rules, then projected onto the direction of interest before aggregating across the token axis.

**Why it matters here:** By identifying which input tokens most drive a specific latent direction (such as the dominant refusal direction), PLRP connects mechanistic interpretability directly to downstream safety behavior, supporting causal claims about what the model's internal axes encode and enabling targeted jailbreak construction via [[trigger-removal-attack]].

**Lineage:** extends the Layer-wise Relevance Propagation family of attribution methods; see [[trigger-removal-attack]] for a direct downstream application.
