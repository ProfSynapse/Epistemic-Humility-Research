---
aliases:
- MLP erasure
- late-layer erasure
- max-likelihood-token downregulation
tags:
- kg/term
- concept
- term
kg:
  id: term:erasure-mlp
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
- '[[hydra-effect]]'
relationships:
- type: proposed_by
  target: '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
  target_id: paper:2307.15771
  confidence: high
- type: related_to
  target: '[[hydra-effect]]'
  target_id: term:hydra-effect
  confidence: high
---

Erasure MLPs are late-layer MLP sublayers that act as a counterbalancing
function, actively downregulating the logit of the current max-likelihood
token rather than only ever boosting it. McGrath et al. (2023) identified
this motif alongside the [[hydra-effect]] in their causal analysis of
factual-recall computations: some late MLP layers systematically suppress
the model's own top prediction, and ablating an upstream attention layer
attenuates this erasure behaviour downstream.

**Why it matters here:** erasure MLPs show that "importance" in a
circuit is not monotonic -- a late component can be causally important
precisely because it is suppressing a signal, not amplifying one. This
complicates naive interpretations of ablation and logit-attribution studies
that assume every component's effect points the same direction as its
final-logit contribution.

**Lineage:** identified via [[causal-effect-decomposition]] of the same
causal-tracing pipeline that surfaced the [[hydra-effect]]; its reduction
under upstream ablation is part of how the network partially restores an
ablated logit.
