---
aliases:
- Compensation decorrelates ablation vs. unembedding importance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:downstream-compensation-decorrelates-ablation-and-unembedding-importance-measures
  type: mechanism
  status: canonical
cause: "Downstream [[hydra-effect]] compensatory response to an attention-layer ablation in [[chinchilla-7b]]"
effect: "Weakens the correlation between ablation-based layer-importance measures and static unembedding-based ([[logit-lens]]-style) importance measures for that layer, since compensation changes what an ablation reveals about a layer's role independent of its own unembedding-space contribution"
polarity: decreases
related:
- '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
- '[[hydra-effect]]'
- '[[logit-lens]]'
- '[[chinchilla-7b]]'
relationships:
- type: supported_by
  target: '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
  target_id: paper:2307.15771
  confidence: high
- type: related_to
  target: '[[hydra-effect]]'
  target_id: term:hydra-effect
  confidence: high
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
  confidence: high
- type: related_to
  target: '[[chinchilla-7b]]'
  target_id: model:chinchilla-7b
---

Because a downstream layer's compensatory response to an ablation (the
[[hydra-effect]]) explains most of the variance in how downstream direct
effects change (92% of variance at the peak layer in [[chinchilla-7b]]), an
importance measure derived from ablating a layer and an importance measure
derived from that layer's static unembedding-space ([[logit-lens]]-style)
contribution stop tracking each other closely: the ablation measure is
confounded by how much downstream compensation absorbs the ablation, while
the unembedding measure is not. This decorrelation is a caution against
treating either measure alone as a faithful proxy for "how much a layer
matters."
