---
aliases:
- concept-cone dimensions beyond DIM are causally effective and near-orthogonal to it
- truth is multi-dimensional but the extra dimensions do not resemble the classic truth direction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:truth-cone-basis-vectors-causally-mediate-truth-orthogonally-to-dim
  type: mechanism
  status: canonical
cause: "Loss-guided concept cone discovery trains a k-dimensional (k=1..5) orthonormal basis at the empirically strongest layer/token position, using a three-term objective (induce truth on activation-addition to false statements, inhibit truth on directional ablation from true statements, retain unrelated behavior via KL divergence to 30-token Alpaca continuations), on Qwen2.5 (3B/7B/14B) and Gemma-2 (2B/9B), then Monte Carlo samples 64 nonnegative combinations of the basis per dimension to estimate Answer Switching Rate (ASR)."
effect: "In the larger models (Qwen-7B, Gemma-9B) ASR stays near 100% across all five cone dimensions with mean Alpaca KL divergence of only 0.026-0.045, while in smaller models (Qwen-3B, Gemma-2B) ASR falls off sharply past dimension 2-3 (e.g. Gemma-2B: 100% at dim 1-2, 53.7% at dim 3, 27.1% at dim 5). At the same time, cosine similarity between each additional cone basis vector and the classic difference-in-means (DIM) truth direction is near zero for every dimension beyond the first (order 1e-1 for v1, order 1e-9 for v2 through v5 in both Gemma-2-9B and Qwen-2.5-9B): the causally effective extra dimensions are geometrically almost orthogonal to the single linear truth direction, not variations of it."
polarity: enables
related:
- '[[2505.21800--directions-cones-exploring-multidimensional-representations-propositional-facts]]'
- '[[truth-concept-cone]]'
- '[[truth-direction]]'
- '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
- '[[answer-switching-rate]]'
relationships:
- type: supported_by
  target: '[[2505.21800--directions-cones-exploring-multidimensional-representations-propositional-facts]]'
  target_id: paper:2505.21800
  confidence: high
  evidence:
  - Table 1 (ASR by model and cone dimension), Table 2 (mean KL divergence),
    Table 3 and Appendix E (cosine similarity between DIM and cone basis vectors)
- type: related_to
  target: '[[truth-concept-cone]]'
  target_id: term:truth-concept-cone
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
- type: related_to
  target: '[[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]]'
  target_id: mechanism:correctness-direction-weakly-identified-defeats-cosine-rotation-probe
  confidence: medium
  evidence:
  - Both results caution against reading a single fitted direction's cosine
    geometry as the whole story for a correctness-adjacent signal, though this
    paper's dissociation is about extra causal dimensions rather than
    within-stage identifiability noise
- type: related_to
  target: '[[answer-switching-rate]]'
  target_id: metric:answer-switching-rate
  confidence: high
---

Truth is not confined to the single direction found by difference-in-means: additional orthonormal basis vectors discovered by loss-guided concept-cone optimization causally flip factual answers at near-ceiling rates in larger models, with minimal collateral drift on unrelated instruction-following, while sitting at near-zero cosine similarity to the original truth direction. Larger models support more of these effective, near-orthogonal dimensions than smaller models do.

**Why it matters here:** it is the closest published demonstration that a truth-adjacent behavioral signal is a genuine causal subspace rather than a single axis, using a causal-intervention readout (ASR, KL-divergence fidelity) rather than a correlational one. It complicates any account that treats the DIM/mass-mean direction as the complete truth representation, and it gives a template (add/ablate/retain loss, Monte Carlo sampling within the cone) for testing whether a correctness signal is similarly multi-dimensional.

**Lineage:** extends [[refusal-concept-cone]]'s cone construction from refusal to [[truth-concept-cone]]; contrasts with the single-axis account in [[truth-direction]]. Distinct from [[correctness-direction-weakly-identified-defeats-cosine-rotation-probe]], which found the correctness direction's own within-stage identity unstable rather than finding additional causal dimensions; both results converge on the same caution against over-trusting a single fitted direction's cosine geometry.
