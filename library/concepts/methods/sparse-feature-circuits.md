---
aliases:
- feature circuits
- sparse feature circuit discovery
tags:
- kg/method
- concept
- method
kg:
  id: method:sparse-feature-circuits
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2403.19647--sparse-feature-circuits]]'
- '[[attribution-patching]]'
- '[[sparse-autoencoder]]'
- '[[shift-feature-trimming]]'
- '[[circuit-faithfulness]]'
- '[[indirect-object-identification]]'
relationships:
- type: proposed_by
  target: '[[2403.19647--sparse-feature-circuits]]'
  target_id: paper:2403.19647
  confidence: high
- type: derived_from
  target: '[[attribution-patching]]'
  target_id: method:attribution-patching
- type: derived_from
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: required_by
  target: '[[shift-feature-trimming]]'
  target_id: method:shift-feature-trimming
---

Sparse feature circuits are causally implicated computational subgraphs of
human-interpretable sparse-autoencoder (SAE) features, plus error terms, that
explain specific language-model behaviors. They are discovered by applying
attribution-patching or integrated-gradients-based linear approximations to
indirect effects across all SAE feature nodes, then thresholding by causal
importance. Unlike neuron- or attention-head-level circuits, each node is
monosemantic and thus directly human-readable, enabling precise mechanistic
accounts of model behaviors.

**Why it matters here:** Sparse feature circuits provide the highest-resolution
causal account currently available for model behaviors; if epistemic states such
as knowing versus not-knowing are mediated by identifiable circuits, this
methodology is the tool to find and manipulate them without side-effects.

**Lineage:** extends [[attribution-patching]] over [[sparse-autoencoder]]
feature nodes; required by [[shift-feature-trimming]] for its debiasing step.
