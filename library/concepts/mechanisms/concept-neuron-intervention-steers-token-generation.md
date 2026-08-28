---
aliases:
- Interpretable neuron activation causally controls generated concepts
- Concept bottleneck values directly steer autoregressive output
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:concept-neuron-intervention-steers-token-generation
  type: mechanism
  status: canonical
cause: "A user sets a target concept neuron's activation high and suppresses the other concept neurons during decoding."
effect: "Autoregressive generation shifts toward tokens and text associated with the selected concept."
polarity: causes
related:
- '[[2412.07992--concept-bottleneck-large-language-models]]'
- '[[concept-bottleneck-layer]]'
- '[[steerability]]'
relationships:
- type: supported_by
  target: '[[2412.07992--concept-bottleneck-large-language-models]]'
  target_id: paper:2412.07992
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

The generation experiments intervene on named sentiment or topic neurons and measure whether 100-token samples follow the selected concept. The toxicity chatbot similarly uses separate query-detection and response-generation neurons and reaches a steerability score of 0.9137.
