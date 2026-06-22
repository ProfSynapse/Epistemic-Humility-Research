---
aliases:
- SHIFT
- Sparse Human-Interpretable Feature Trimming
- SHIFT (Spurious Human-Interpretable Feature Trimming)
tags:
- kg/method
- concept
- method
kg:
  id: method:shift-feature-trimming
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2403.19647--sparse-feature-circuits]]'
- '[[sparse-feature-circuits]]'
- '[[sparse-autoencoder]]'
- '[[bias-in-bios]]'
relationships:
- type: proposed_by
  target: '[[2403.19647--sparse-feature-circuits]]'
  target_id: paper:2403.19647
  confidence: high
- type: derived_from
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
- type: related_to
  target: '[[bias-in-bios]]'
  target_id: dataset:bias-in-bios
---

SHIFT (Spurious Human-Interpretable Feature Trimming) is a debiasing procedure
that (1) discovers a sparse feature circuit for a classifier using
sparse-autoencoder features, (2) has a human annotator label each feature node
as task-relevant or spurious, and (3) ablates the spurious feature nodes to
redirect classifier generalization. The method requires no disambiguating labeled
data and no prior knowledge of what the spurious signal is, making it applicable
wherever a circuit can be found and a human can judge feature semantics.

**Why it matters here:** SHIFT demonstrates that circuit-level mechanistic
understanding can be converted into targeted behavioral interventions without
full retraining, a design principle directly applicable to correcting spurious
abstention triggers or sycophancy patterns in epistemic-humility research.

**Lineage:** derives from [[sparse-feature-circuits]]; validated on the
[[bias-in-bios]] gender-bias setting as introduced in
[[2403.19647--sparse-feature-circuits]].
