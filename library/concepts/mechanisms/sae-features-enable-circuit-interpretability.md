---
aliases:
- SAE features enable human-interpretable circuits
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sae-features-enable-circuit-interpretability
  type: mechanism
  status: canonical
cause: Replacing polysemantic neurons with monosemantic SAE features as circuit nodes
effect: Circuits become human-interpretable and useful for downstream editing tasks such as classifier debiasing
polarity: enables
related:
- '[[2403.19647--sparse-feature-circuits]]'
- '[[sparse-feature-circuits]]'
- '[[sparse-autoencoder]]'
- '[[monosemanticity]]'
- '[[bias-in-bios]]'
relationships:
- type: supported_by
  target: '[[2403.19647--sparse-feature-circuits]]'
  target_id: paper:2403.19647
  confidence: high
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
- type: related_to
  target: '[[bias-in-bios]]'
  target_id: dataset:bias-in-bios
---

[[sparse-feature-circuits]] replace polysemantic neurons with monosemantic [[sparse-autoencoder]] features as the atomic nodes of circuit analysis, enabling circuits whose components can be described in plain language (arXiv:2403.19647). On the [[bias-in-bios]] profession-classification task, this interpretability proves actionable: a human can inspect the circuit, identify features that encode spurious gender correlations, and ablate them to improve worst-group accuracy without access to disambiguating labeled data. The downstream utility for debiasing demonstrates that human interpretability of circuit nodes is a prerequisite for guided circuit-level intervention.
