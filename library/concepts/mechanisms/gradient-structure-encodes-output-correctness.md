---
aliases:
- gradient structure encodes output correctness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gradient-structure-encodes-output-correctness
  type: mechanism
  status: canonical
cause: "Computing layer-wise gradient patterns from a single forward-backward pass over a model's own generated answer."
effect: "A lightweight classifier predicts hallucinations and model abstention more accurately than confidence-based or sampling-based signals."
polarity: enables
related:
- '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
- '[[grad-detect]]'
- '[[hallucination]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
  target_id: paper:2606.24790
  confidence: high
- type: related_to
  target: '[[grad-detect]]'
  target_id: method:grad-detect
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

Kamat et al. report that the internal gradient structure of an LLM, captured in
one backward pass over its own answer, carries information about the correctness
of that answer which is not recoverable from output-level signals alone. A
classifier trained on these per-layer gradient features beats confidence-based
and sampling-based baselines on both hallucination detection and model
abstention prediction across eleven models and four Q&A benchmarks. This rhymes
with activation-side results such as the internal state knowing when a model is
lying, but locates the usable signal in gradients rather than activations.
