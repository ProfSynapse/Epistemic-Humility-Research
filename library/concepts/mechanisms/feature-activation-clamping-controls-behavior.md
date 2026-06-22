---
aliases:
- Feature clamping causally controls model behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:feature-activation-clamping-controls-behavior
  type: mechanism
  status: canonical
cause: Artificially clamping a [[sparse-autoencoder]] feature activation to high or low values during the forward pass via [[activation-intervention]]
effect: Model output shifts in a specific, interpretable direction consistent with the feature's semantic interpretation -- for example, clamping a Golden Gate Bridge feature causes self-identification as the bridge, and clamping an internal-conflict feature causes the model to reveal suppressed information
polarity: enables
related:
- '[[tc2024--scaling-monosemanticity]]'
- '[[sparse-autoencoder]]'
- '[[feature-steering]]'
- '[[activation-intervention]]'
relationships:
- type: supported_by
  target: '[[tc2024--scaling-monosemanticity]]'
  target_id: paper:tc2024
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[feature-steering]]'
  target_id: method:feature-steering
- type: related_to
  target: '[[activation-intervention]]'
  target_id: method:activation-intervention
---

Templeton et al. (tc2024) show that setting SAE feature activations to fixed values mid-forward-pass produces targeted, semantically coherent changes in model behavior, confirming a causal role for individual features. Clamping the Golden Gate Bridge feature causes Claude 3 Sonnet to identify as the bridge regardless of context, and clamping a sycophantic praise feature induces exaggerated flattery. These interventions establish that SAE features are not merely correlational probes but causally upstream of specific model outputs.
