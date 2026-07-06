---
aliases:
- stages of inference
- detokenization
- residual sharpening
- prediction ensembling
tags:
- kg/term
- concept
- term
kg:
  id: term:stages-of-inference
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2406.19384--remarkable-robustness-llms-stages-inference]]'
- '[[iterative-inference]]'
- '[[residual-stream-refinement]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2406.19384--remarkable-robustness-llms-stages-inference]]'
  target_id: paper:2406.19384
  confidence: high
- type: related_to
  target: '[[iterative-inference]]'
  target_id: term:iterative-inference
  confidence: high
- type: related_to
  target: '[[residual-stream-refinement]]'
  target_id: term:residual-stream-refinement
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Stages of inference is the hypothesis that decoder-only LLM computation proceeds
in four ordered, depth-dependent regimes operating on the residual stream:
detokenization (early layers integrate local context to lift raw tokens into
coherent entities), feature engineering (middle layers iteratively refine task
and entity features), prediction ensembling (later layers aggregate features into
next-token predictions), and residual sharpening (final layers suppress obsolete
features to finalize the distribution). Lad et al. find these stages recur across
eight-plus model families and that middle layers are remarkably robust to
deletion and adjacent swapping (72 to 95% accuracy retained), while final layers
show rising MLP-output norm and falling entropy that mark the sharpening phase.

**Why it matters here:** stages of inference tells the census what per-layer
displacement is expected structure rather than anomaly. Early-layer displacement
is local detokenization, middle-layer displacement is low-magnitude and near-
interchangeable, and a large late-layer displacement oriented toward the
unembedding is the sharpening signature. The anomaly-hunting baseline must be
depth-conditioned.

**Lineage:** a discrete decomposition of [[iterative-inference]] into four
phases; residual sharpening specializes [[residual-stream-refinement]]; all
operate on the [[residual-stream]].
