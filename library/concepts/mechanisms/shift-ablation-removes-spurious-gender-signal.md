---
aliases:
- SHIFT ablation removes spurious gender dependence without labeled data
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:shift-ablation-removes-spurious-gender-signal
  type: mechanism
  status: canonical
cause: Human-guided ablation of spurious SAE features identified via sparse feature circuit on an ambiguous (gender-predictive) training set
effect: Classifier worst-group profession accuracy rises from 24.4% (original) to 76.0% (SHIFT) or 89.0% (SHIFT + retrain), while gender accuracy drops from 87.4% to 54.0%/52.0%, without access to disambiguating labeled data
polarity: enables
related:
- '[[2403.19647--sparse-feature-circuits]]'
- '[[sparse-feature-circuits]]'
- '[[shift-feature-trimming]]'
- '[[bias-in-bios]]'
- '[[sae-features-enable-circuit-interpretability]]'
relationships:
- type: supported_by
  target: '[[2403.19647--sparse-feature-circuits]]'
  target_id: paper:2403.19647
  confidence: high
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
- type: related_to
  target: '[[shift-feature-trimming]]'
  target_id: method:shift-feature-trimming
- type: related_to
  target: '[[bias-in-bios]]'
  target_id: dataset:bias-in-bios
- type: related_to
  target: '[[sae-features-enable-circuit-interpretability]]'
  target_id: mechanism:sae-features-enable-circuit-interpretability
---

[[shift-feature-trimming]] (SHIFT) uses the interpretability of sparse feature circuits to debias a profession classifier without access to gender-balanced labels: a human inspects the circuit identified on the [[bias-in-bios]] ambiguous training set, flags SAE features that encode gender-correlated signals, and ablates them at inference time (arXiv:2403.19647). This targeted ablation raises worst-group profession accuracy from 24.4% to 76.0%, and combining SHIFT with retraining on the ablated representation reaches 89.0%, while gender prediction accuracy falls from 87.4% to approximately 52% (near chance). The result demonstrates that circuit interpretability can substitute for curated debiasing datasets when the spurious signal is localizable to identifiable monosemantic features.
