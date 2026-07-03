---
aliases:
- MetaSAE joint training improves automated interpretability fuzzing scores
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:metasae-improves-fuzzing-scores
  type: mechanism
  status: canonical
cause: "MetaSAE joint training with [[decomposability-penalty]] producing more atomic feature directions in the primary [[sparse-autoencoder]]"
effect: "7.6% improvement in fuzzing scores (automated interpretability) on GPT-2 large layer 20, validated independently of the co-occurrence training metric"
polarity: increases
related:
- '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
- '[[metasae]]'
- '[[sparse-autoencoder]]'
- '[[decomposability-penalty]]'
relationships:
- type: supported_by
  target: '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
  target_id: paper:2604.03436
  confidence: high
- type: related_to
  target: '[[metasae]]'
  target_id: method:metasae
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

The MetaSAE decomposability penalty not only reduces latent co-occurrence during training but also improves the quality of the resulting features as measured by automated interpretability fuzzing. On GPT-2 large layer 20, the penalty yields a 7.6% gain in fuzzing scores relative to a baseline SAE trained without the penalty (arXiv:2604.03436). Because fuzzing is assessed independently of the co-occurrence objective, this result confirms that the atomicity induced by the penalty corresponds to genuinely more interpretable feature directions rather than a training artefact.
