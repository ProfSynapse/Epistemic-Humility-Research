---
aliases:
- depth scaling spreads computation rather than composing new computation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:depth-scaling-spreads-computation-rather-than-composing-new
  type: mechanism
  status: canonical
cause: "increasing model depth within the same architecture family (more transformer layers at comparable width/training regime)."
effect: "linear maps between the residual streams of a shallow and a deep sibling model achieve lowest prediction error along the relative-depth diagonal (layers at matched fractional depth correspond best), indicating the deeper model spreads the same kind of computation over more layers rather than composing qualitatively new, higher-order computation."
polarity: redistributes
related:
- '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
- '[[cross-model-layer-correspondence-probing]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
  target_id: paper:2505.13898
  confidence: high
- type: related_to
  target: '[[cross-model-layer-correspondence-probing]]'
  target_id: method:cross-model-layer-correspondence-probing
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Training linear maps from every layer of Qwen 2.5 1.5B's residual stream to
every layer of the independently trained Qwen 2.5 14B's residual stream
produces a clear diagonal pattern of lowest error, showing that layers at
matched relative depth correspond best across the two models. Csordás et al.
read this as evidence that adding depth within a model family mostly
fine-grains the same computation over more layers instead of unlocking new
kinds of composition, which they offer as a partial explanation for why
increasing depth yields diminishing returns.

**Lineage:** the central finding produced by
[[cross-model-layer-correspondence-probing]]; complements
[[second-half-layers-refine-without-composing]] as a second, cross-model line
of evidence against depth being used for compositional computation.
