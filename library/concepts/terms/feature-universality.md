---
aliases:
- universality of SAE features
tags:
- kg/term
- concept
- term
kg:
  id: term:feature-universality
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[tc2023--towards-monosemanticity]]'
- '[[sparse-autoencoder]]'
- '[[monosemanticity]]'
relationships:
- type: proposed_by
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
---

Feature universality is the finding that sparse autoencoder features learned from different transformer models trained with different random seeds are substantially similar to each other, more so than those models' own individual neurons are. In the work that documented it, matched SAE features across two one-layer transformers had a median activation correlation of 0.72, compared to 0.46 for the corresponding neurons. This convergence across seeds is interpreted as evidence that SAE features reflect genuine recurring structures in the space of learned representations rather than being arbitrary artifacts of a particular training run.

**Why it matters here:** If representations of uncertainty or self-knowledge are universal across model seeds, then mechanistic findings about calibration and abstention should generalize rather than being seed-specific accidents, which raises the scientific tractability of the research program.

**Lineage:** introduced in [[tc2023--towards-monosemanticity]] as a companion finding to [[monosemanticity]] and [[feature-splitting]].
