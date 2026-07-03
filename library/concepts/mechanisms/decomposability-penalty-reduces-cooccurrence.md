---
aliases:
- Decomposability penalty reduces SAE latent co-occurrence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:decomposability-penalty-reduces-cooccurrence
  type: mechanism
  status: canonical
cause: "Joint training of a primary [[sparse-autoencoder]] with a [[decomposability-penalty]] (MetaSAE) that penalises correlated latent activations"
effect: "Reduction in mean |φ| co-occurrence metric, indicating more statistically independent SAE latent activations"
polarity: decreases
related:
- '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
- '[[sparse-autoencoder]]'
- '[[decomposability-penalty]]'
- '[[metasae]]'
relationships:
- type: supported_by
  target: '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
  target_id: paper:2604.03436
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[decomposability-penalty]]'
  target_id: method:decomposability-penalty
- type: related_to
  target: '[[metasae]]'
  target_id: method:metasae
---

When a secondary MetaSAE is trained jointly with a primary SAE and a decomposability penalty forces latent co-occurrences toward zero, the resulting primary SAE latents fire more independently from one another. The MetaSAE paper (arXiv:2604.03436) measures this via the mean |φ| co-occurrence metric and shows a systematic reduction at moderate penalty strengths before reconstruction degrades. This mechanism is the training-time counterpart to improved atomic interpretability observed at inference time.
