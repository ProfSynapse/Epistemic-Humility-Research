---
aliases:
- zero-shot accuracy
- zero-shot performance
- novel context accuracy
- Zero-Shot Generalization Accuracy
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:zero-shot-compositional-generalization
  type: metric
  status: canonical
area: neuroscience
related: []
relationships: []
---

Zero-shot compositional generalization measures task accuracy on C-PRO (Compositional
Paired-Rule Object) contexts that were never encountered during training, without any
additional fine-tuning on those contexts. It tests whether a model has formed abstract,
transferable representations of the underlying rule structure rather than memorizing
surface-level input-output mappings. Performance near ceiling on held-out rule
combinations is evidence that the learned representation is genuinely compositional and
supports immediate transfer to novel combinations.

**Why it matters here:** A model whose abstention or hedging behavior generalizes
zero-shot to novel epistemic combinations (new pairings of uncertainty type and domain)
demonstrates that its self-knowledge is driven by abstract internal structure rather than
pattern-matched heuristics, which is a precondition for robust [[epistemic-humility]].

**Lineage:** no upstream lineage; reported alongside [[ood-coefficient-of-determination]]
as a primary behavioral measure of compositional transfer.
