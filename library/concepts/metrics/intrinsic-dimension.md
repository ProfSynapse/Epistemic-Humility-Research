---
aliases:
- intrinsic dimension
- local intrinsic dimension
- LID
- TwoNN estimator
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:intrinsic-dimension
  type: metric
  status: canonical
area: metrics
related:
- '[[2506.01034--less-more-local-intrinsic-dimensions-contextual-language]]'
- '[[representation-manifold]]'
- '[[fraction-of-variance-unexplained]]'
relationships:
- type: proposed_by
  target: '[[2506.01034--less-more-local-intrinsic-dimensions-contextual-language]]'
  target_id: paper:2506.01034
  confidence: high
- type: related_to
  target: '[[representation-manifold]]'
  target_id: term:representation-manifold
  confidence: high
- type: related_to
  target: '[[fraction-of-variance-unexplained]]'
  target_id: metric:fraction-of-variance-unexplained
  confidence: low
---

Intrinsic dimension is the dimensionality of the low-dimensional manifold on
which high-ambient-dimensional contextual embeddings actually lie, far below the
ambient hidden size. Ruppik et al. introduce the local intrinsic dimension (LID),
a per-token measure that applies the TwoNN estimator (which infers dimension from
the ratio of each point's first- and second-nearest-neighbor distances) to a
token's local neighborhood. They report mean LID of roughly 8 to 10 in a 768-
dimensional space, that LID drops on the fine-tuning distribution only, and that
falling mean LID tracks and predicts training milestones such as grokking and
convergence.

**Why it matters here:** the intrinsic dimension (or its PCA participation-ratio
cousin) is the quantitative low-versus-high verdict for the census residual. A
sharp PCA elbow or small effective dimension means the out-of-span displacement
lives on a low-dimensional manifold (structured, interpretable); a flat, heavy-
tailed spectrum means a high-dimensional dense component consistent with noise or
nonlinear SAE error.

**Lineage:** measures the dimensionality of a [[representation-manifold]];
complements [[fraction-of-variance-unexplained]] as a spectrum-based
signal-versus-noise separator; the quantitative successor to Cai et al.'s
cluster-and-manifold observation on anisotropic embedding spaces.
