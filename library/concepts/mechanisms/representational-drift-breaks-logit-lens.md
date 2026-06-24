---
aliases:
- Representational drift causes logit lens bias and failure
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:representational-drift-breaks-logit-lens
  type: mechanism
  status: canonical
cause: Transformer hidden states exhibit representational drift (rogue dimensions, shifting covariance across layers) that is not corrected by the fixed unembedding matrix
effect: The logit lens produces biased, systematically predictable output distributions and fails to elicit interpretable predictions for models like BLOOM and OPT
polarity: enables
related:
- '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
- '[[logit-lens]]'
- '[[tuned-lens]]'
- '[[residual-stream]]'
- '[[representational-drift]]'
relationships:
- type: supported_by
  target: '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
  target_id: paper:2303.08112
  confidence: high
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[representational-drift]]'
  target_id: term:representational-drift
---

The [[logit-lens]] applies the final unembedding matrix directly to intermediate hidden states to elicit layer-by-layer predictions, but [[representational-drift]] -- systematic shifts in the geometry of the residual stream across layers, including rogue high-variance dimensions and changing covariance structure -- means the fixed unembedding is miscalibrated for early and middle layers (arXiv:2303.08112). For some models (BLOOM, OPT), this drift is severe enough that the logit lens produces persistently biased distributions that are easily predictable from position alone, undermining interpretability. The failure mode is not random noise but systematic bias, which makes the logit lens unreliable as a diagnostic tool for these architectures.
