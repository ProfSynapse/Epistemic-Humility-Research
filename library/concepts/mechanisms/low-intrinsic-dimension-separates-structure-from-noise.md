---
aliases:
- intrinsic dimension separates low-dimensional structure from dense noise
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:low-intrinsic-dimension-separates-structure-from-noise
  type: mechanism
  status: canonical
cause: "estimating the effective or local intrinsic dimension of a representation point cloud."
effect: "a small intrinsic dimension relative to ambient signals a genuine low-dimensional manifold, while a flat heavy-tailed spectrum signals a dense high-dimensional component."
polarity: enables
related:
- '[[2506.01034--less-more-local-intrinsic-dimensions-contextual-language]]'
- '[[intrinsic-dimension]]'
- '[[representation-manifold]]'
relationships:
- type: supported_by
  target: '[[2506.01034--less-more-local-intrinsic-dimensions-contextual-language]]'
  target_id: paper:2506.01034
  confidence: high
- type: related_to
  target: '[[intrinsic-dimension]]'
  target_id: metric:intrinsic-dimension
  confidence: high
- type: related_to
  target: '[[representation-manifold]]'
  target_id: term:representation-manifold
  confidence: medium
---

Ruppik et al. show that contextual embeddings have local intrinsic dimension
around 8 to 10 in a 768-dimensional space, orders of magnitude below ambient, and
that the neighbor-ratio TwoNN estimate is robust to added noise, so intrinsic
dimension gives a quantitative low-versus-high verdict separating a genuine low-
dimensional manifold from a dense noise-like component.
