---
aliases:
- Typed IIT
- Typed Interchange Intervention Training
tags:
- kg/method
- concept
- method
kg:
  id: method:typed-interchange-intervention-training
  type: method
  status: canonical
area: methods
related:
- '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
- '[[interchange-intervention-training]]'
relationships:
- type: proposed_by
  target: '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
  target_id: paper:2112.00826
  confidence: high
- type: derived_from
  target: '[[interchange-intervention-training]]'
  target_id: method:interchange-intervention-training
  confidence: high
---

Typed interchange intervention training extends IIT by swapping representations across different aligned variables that share a value space. The paper uses these cross-position swaps to enforce common causal roles.

**Why it matters here:** Typed interventions test whether a learned internal variable generalizes across compatible sites instead of working only at one fixed site.

**Lineage:** It is a typed extension of interchange intervention training.
