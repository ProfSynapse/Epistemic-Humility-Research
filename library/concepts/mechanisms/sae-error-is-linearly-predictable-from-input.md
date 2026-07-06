---
aliases:
- most SAE reconstruction error is linearly predictable from the input activation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sae-error-is-linearly-predictable-from-input
  type: mechanism
  status: canonical
cause: "fitting an optimal linear map from the input activation to the SAE reconstruction error."
effect: "recovers about half the error vector and more than 90% of its norm, leaving a smaller dense nonlinear residual."
polarity: enables
related:
- '[[2410.14670--decomposing-dark-matter-sparse-autoencoders]]'
- '[[sae-dark-matter]]'
- '[[nonlinear-sae-error]]'
relationships:
- type: supported_by
  target: '[[2410.14670--decomposing-dark-matter-sparse-autoencoders]]'
  target_id: paper:2410.14670
  confidence: high
- type: related_to
  target: '[[sae-dark-matter]]'
  target_id: term:sae-dark-matter
  confidence: high
- type: related_to
  target: '[[nonlinear-sae-error]]'
  target_id: term:nonlinear-sae-error
  confidence: high
---

Engels et al. show that an optimal linear map from the input activation predicts
about half of the SAE error vector and more than 90% of its norm (norm-probe
R-squared 0.7 to 0.95 at mid layers), so most SAE dark matter is structured, not
noise; the un-predictable remainder is the denser nonlinear error that stays
roughly constant as SAE width grows.
