---
aliases:
- Orthogonal unknown features reduce concept bottleneck leakage
- Unknown-concept separation preserves steering
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:unknown-concept-orthogonality-preserves-bottleneck-control
  type: mechanism
  status: canonical
cause: "An unknown-concept embedding retains unannotated information while an orthogonality loss discourages it from duplicating the known concept embeddings."
effect: "The generator keeps residual capacity without fully bypassing the named bottleneck, improving steerability and preserving generation quality."
polarity: enables
related:
- '[[openreview-L9U5MJJleF--concept-bottleneck-generative-models]]'
- '[[concept-bottleneck-generative-model]]'
- '[[concept-bottleneck-layer]]'
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
---

The ablation study reduced average steerability from 25.6 to 19.9 without the orthogonality loss. Removing the unknown embedding reduced steerability to 16.5 and degraded FID from the CB-GAN reference to 44.1, supporting separate roles for residual capacity and known-unknown separation.
