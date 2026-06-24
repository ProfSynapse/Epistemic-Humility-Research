---
aliases:
- activation steering via SAE features
- clamping feature activations
tags:
- kg/method
- concept
- method
kg:
  id: method:feature-steering
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[tc2023--towards-monosemanticity]]'
- '[[sparse-autoencoder]]'
- '[[activation-addition]]'
- '[[representation-engineering]]'
relationships:
- type: proposed_by
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
- type: derived_from
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[activation-addition]]'
  target_id: method:activation-addition
- type: related_to
  target: '[[representation-engineering]]'
  target_id: method:representation-engineering
---

Feature steering is an intervention method that clamps specific sparse autoencoder feature activations to artificially high or low values during a model's forward pass, then observes the resulting change in output behavior. By holding a feature constant at a value far outside its natural range, researchers can test whether the feature's natural-language interpretation matches its causal role in driving generations. The method provides a causal complement to the correlational evidence from activation analysis alone.

**Why it matters here:** Feature steering applied to uncertainty-related or self-knowledge features would allow causal testing of whether those features genuinely control abstention behavior, which is directly relevant to the mechanistic interpretability strand of the epistemic humility research program.

**Lineage:** extends [[sparse-autoencoder]] dictionary learning with a causal intervention step; related to [[activation-addition]] and [[representation-engineering]] as the broader family of activation-space intervention methods.
