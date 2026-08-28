---
aliases:
- CBGM
- CBGMs
- Concept Bottleneck Generative Models
- concept-bottleneck generative model
tags:
- kg/method
- concept
- method
kg:
  id: method:concept-bottleneck-generative-model
  type: method
  status: canonical
area: methods
related:
- '[[openreview-L9U5MJJleF--concept-bottleneck-generative-models]]'
- '[[concept-bottleneck-layer]]'
- '[[concept-bottleneck-large-language-model]]'
relationships:
- type: proposed_by
  target: '[[openreview-L9U5MJJleF--concept-bottleneck-generative-models]]'
  target_id: paper:openreview-L9U5MJJleF
  confidence: high
- type: required_by
  target: '[[concept-bottleneck-layer]]'
  target_id: term:concept-bottleneck-layer
  confidence: high
- type: related_to
  target: '[[concept-bottleneck-large-language-model]]'
  target_id: method:concept-bottleneck-large-language-model
  confidence: high
---

Concept Bottleneck Generative Models insert a supervised concept-embedding layer inside a GAN, VAE, or diffusion model. Named concept embeddings and a separate unknown-concept embedding feed the remaining generator. A concept loss trains the named predictions, and an orthogonality loss separates the unknown path from the known concept embeddings.

**Why it matters here:** The design puts supervised internal concept values on the causal generation path and makes those values directly adjustable at inference time.

**Lineage:** It adapts the [[concept-bottleneck-layer]] and concept-embedding architecture to image-generative models. The later [[concept-bottleneck-large-language-model]] applies a related bottleneck idea to text classification and autoregressive generation.
