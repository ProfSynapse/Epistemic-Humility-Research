---
aliases:
- Intermediate Layer Distributions Converge Progressively to Final Output
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:layers-converge-to-output-distribution
  type: mechanism
  status: canonical
cause: Iterative refinement across transformer layers operating in a shared predictive embedding space via [[residual-stream]] accumulation
effect: Distributions decoded from intermediate layers via the [[logit-lens]] move from rough or nonsensical guesses in early layers to high-quality predictions that match or nearly match the final output well before the last layer
polarity: enables
related:
- '[[ll2020--interpreting-gpt-the-logit-lens]]'
- '[[logit-lens]]'
- '[[residual-stream]]'
- '[[iterative-refinement-transformers]]'
relationships:
- type: supported_by
  target: '[[ll2020--interpreting-gpt-the-logit-lens]]'
  target_id: paper:ll2020
  confidence: high
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[iterative-refinement-transformers]]'
  target_id: term:iterative-refinement-transformers
---

Nostalgebraist (ll2020) shows that logit-lens projections of the residual stream improve monotonically across layers in GPT-2, with the final answer often identifiable from the middle layers onward. Early layers produce plausible but imprecise token distributions, while later layers sharpen them toward the model's committed prediction. This progressive convergence supports an iterative-refinement view of transformer computation in which each layer incrementally improves a shared draft rather than computing from scratch.
