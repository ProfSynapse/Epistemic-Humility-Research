---
aliases:
- Bottleneck probability replacement steers image concepts
- Concept embedding interpolation controls generated attributes
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:concept-probability-intervention-steers-generative-output
  type: mechanism
  status: canonical
cause: "A user replaces a bottleneck concept probability, changing the convex mixture of that concept's active and inactive embeddings."
effect: "The post-bottleneck network generates an output with a shifted level of the selected concept while preserving other image content."
polarity: causes
related:
- '[[openreview-L9U5MJJleF--concept-bottleneck-generative-models]]'
- '[[concept-bottleneck-generative-model]]'
- '[[concept-bottleneck-layer]]'
- '[[steerability]]'
relationships:
- type: supported_by
  target: '[[openreview-L9U5MJJleF--concept-bottleneck-generative-models]]'
  target_id: paper:openreview-L9U5MJJleF
  confidence: high
- type: related_to
  target: '[[concept-bottleneck-generative-model]]'
  target_id: method:concept-bottleneck-generative-model
  confidence: high
- type: related_to
  target: '[[concept-bottleneck-layer]]'
  target_id: term:concept-bottleneck-layer
  confidence: high
- type: related_to
  target: '[[steerability]]'
  target_id: metric:steerability
  confidence: high
---

Across concept-bottleneck GAN, VAE, and diffusion models, interventions on the named concept probabilities changed generated attributes more often than the corresponding conditional-generation baselines. The advantage persisted when the number of annotated concepts increased.
