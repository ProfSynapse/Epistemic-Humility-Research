---
aliases:
- Judge bias forms low-dimensional type-specific activation subspaces
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:judge-bias-forms-type-specific-low-dimensional-subspaces
  type: mechanism
  status: canonical
cause: "Semantics-irrelevant bias cues alter an LLM judge's final-token residual-stream activations."
effect: "Biased inputs leave the baseline activation manifold along low-dimensional, bias-type-specific directions that sharpen with model depth."
polarity: enables
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[llm-judge-scoring-bias]]'
- '[[representation-manifold]]'
- '[[residual-stream-activation]]'
relationships:
- type: supported_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[llm-judge-scoring-bias]]'
  target_id: term:llm-judge-scoring-bias
  confidence: high
- type: related_to
  target: '[[representation-manifold]]'
  target_id: term:representation-manifold
  confidence: high
- type: related_to
  target: '[[residual-stream-activation]]'
  target_id: term:residual-stream-activation
  confidence: high
---

MDS and PCA analyses separate biased inputs from the baseline manifold, while per-sample displacement vectors become increasingly separable by bias type at deeper layers. The estimated effective dimensionality is 3-5 directions per bias type at Llama-3.1-8B layer 25, and the geometric pattern is reported across Llama, Qwen, and Gemma judges.
