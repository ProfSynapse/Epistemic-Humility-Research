---
aliases:
- MetaSAEs
- joint SAE training with decomposability penalty
- joint primary-meta SAE training
- meta-sparse-autoencoder
- Meta-SAE
- meta sae
tags:
- kg/method
- concept
- method
kg:
  id: method:metasae
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
- '[[sparse-autoencoder]]'
- '[[polysemanticity]]'
relationships:
- type: proposed_by
  target: '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
  target_id: paper:2604.03436
  confidence: high
- type: derived_from
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
---

A joint training objective for sparse autoencoders in which a small meta SAE is
trained simultaneously alongside the primary SAE to sparsely reconstruct the
primary SAE's decoder columns. The primary SAE is penalized whenever its decoder
directions are easily reconstructed by the meta dictionary, creating gradient
pressure toward more mutually independent feature directions that resist sparse
meta-compression. On GPT-2 large (layer 20), the best configuration
(lambda_2=0.3, sigma^2=1.0) reduces mean |phi| by 7.5% and improves fuzzing
scores by 7.6% relative to an identical solo SAE.

**Why it matters here:** More atomic SAE features have cleaner causal semantics;
if internal epistemic states such as doubt or answerability are encoded in
overlapping polysemantic features, MetaSAE training is one path toward separating
them for reliable readout or steering.

**Lineage:** derives from [[sparse-autoencoder]]; addresses [[polysemanticity]]
through a joint training pressure rather than post-hoc diagnosis; the
[[decomposability-penalty]] is the per-feature loss term that implements this
pressure.
