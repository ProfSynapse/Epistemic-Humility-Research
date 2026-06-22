---
aliases:
- MLP as key-value memory
- feed-forward associative memory
- factual storage in FFN
- Mid-layer feed-forward knowledge storage
- mid layer ffn knowledge storage
- transformer FFN key-value memory
- feed-forward network memory
- FFN memory
- FFN as Key-Value Memory
tags:
- kg/term
- concept
- term
kg:
  id: term:ffn-as-key-value-memory
  type: term
  status: canonical
area: mechanistic-interpretability
related: []
relationships: []
---

The FFN-as-key-value-memory framing holds that the weight matrices of
feed-forward (MLP) sublayers in transformer models function as two-layer
associative memories: the first (key) matrix pattern-matches on input
representations and the second (value) matrix reads out a memorized output
vector. Empirical work on GPT-family models finds that factual associations are
preferentially stored in middle-to-upper MLP layers at the final token position
of the subject phrase, making those weights the locus of knowledge editing
interventions.

**Why it matters here:** If factual knowledge is localized in identifiable
weights, the question of what a model "knows" becomes more tractable, informing
theories of the knowledge boundary and why fine-tuning on unknown facts induces
hallucination rather than calibrated abstention.

**Lineage:** foundational term underlying [[model-editing]], [[rank-one-model-editing]],
and [[knowledge-neurons]]; related to [[mid-layer-mlp-mediates-factual-recall]].
