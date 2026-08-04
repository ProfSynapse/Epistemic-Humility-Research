---
aliases:
- second-half layers refine output without composing subresults
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:second-half-layers-refine-without-composing
  type: mechanism
  status: canonical
cause: "a layer's position in the second half of a deep transformer's stack, past the midpoint contribution drop."
effect: "skipping the layer leaves later layers' contributions and future-token predictions almost unchanged, yet the layer remains highly important for the current token's output, and logit-lens KL-to-final falls with rising top-5 overlap across the same layers -- refinement of the existing prediction rather than construction of reusable subresults for later computation."
polarity: limits
related:
- '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
- '[[stages-of-inference]]'
- '[[iterative-inference]]'
- '[[residual-stream-refinement]]'
relationships:
- type: supported_by
  target: '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
  target_id: paper:2505.13898
  confidence: high
- type: related_to
  target: '[[stages-of-inference]]'
  target_id: term:stages-of-inference
  confidence: high
- type: related_to
  target: '[[iterative-inference]]'
  target_id: term:iterative-inference
  confidence: high
- type: related_to
  target: '[[residual-stream-refinement]]'
  target_id: term:residual-stream-refinement
  confidence: medium
---

Csordás et al. show that layers in the second half of Llama 3.1, Qwen 3, and
OLMo 2 models contribute much less to the residual stream than first-half
layers, and that skipping second-half layers barely perturbs later layers'
contributions or future-token predictions, even though those same layers stay
causally important for the current token. Logit-lens diagnostics confirm the
second half is mostly sharpening the existing output distribution (falling
KL-divergence to the final prediction, rising top-5 overlap) rather than
computing subresults that later layers or later tokens will reuse. This is a
sharper, causally verified version of the [[iterative-inference]] /
[[stages-of-inference]] picture: depth in the back half buys refinement of the
current guess, not composition of new computation.

**Lineage:** specializes [[stages-of-inference]]'s residual-sharpening account
with causal (skip/erase) evidence rather than correlational norm and entropy
trends; a limiting case of [[residual-stream-refinement]] in which refinement
stops contributing to anything beyond the current token.
