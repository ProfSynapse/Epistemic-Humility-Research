---
aliases:
- Zero IIT loss entails causal abstraction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:iit-zero-loss-entails-causal-abstraction
  type: mechanism
  status: canonical
cause: "Interchange intervention training loss is zero for all aligned source and base inputs."
effect: "The high-level causal model is a causal abstraction of the neural model under the specified alignment and output mapping."
polarity: enables
related:
- '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
- '[[interchange-intervention-training]]'
- '[[causal-abstraction]]'
relationships:
- type: supported_by
  target: '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
  target_id: paper:2112.00826
  confidence: high
- type: related_to
  target: '[[interchange-intervention-training]]'
  target_id: method:interchange-intervention-training
  confidence: high
- type: related_to
  target: '[[causal-abstraction]]'
  target_id: term:causal-abstraction
  confidence: high
---

The paper proves this implication in Appendix A. The converse does not necessarily hold, so a neural model can realize the abstraction without attaining zero training loss.
