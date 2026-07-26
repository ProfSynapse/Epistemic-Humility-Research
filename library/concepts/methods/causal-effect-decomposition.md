---
aliases:
- direct/indirect effect decomposition
- causal mediation analysis (circuits)
tags:
- kg/method
- concept
- method
kg:
  id: method:causal-effect-decomposition
  type: method
  status: canonical
area: methods
related:
- '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
- '[[activation-patching]]'
- '[[logit-lens]]'
relationships:
- type: proposed_by
  target: '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
  target_id: paper:2307.15771
  confidence: medium
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: high
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
  confidence: medium
---

Causal effect decomposition splits a component's total causal effect on the
output logit into a direct effect (the component's own contribution when
downstream components are held fixed) and an indirect/compensatory effect
(the change in downstream components' contributions caused by an upstream
intervention). McGrath et al. (2023) apply this decomposition layer-by-layer
in Chinchilla 7B to separate a layer's own contribution to the
max-likelihood-token logit from the knock-on change it induces in other
layers, which is how they isolate and quantify the [[hydra-effect]].

**Why it matters here:** without decomposing direct from compensatory
effects, an ablation study conflates "this component matters" with "this
component matters and nothing else changed," which is false whenever
downstream compensation (the [[hydra-effect]]) or erasure-MLP attenuation is
present.

**Lineage:** builds on [[activation-patching]] causal-intervention machinery
and is read out via [[logit-lens]]-style projection of intermediate states
into vocabulary space.
