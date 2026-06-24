---
aliases:
- dictionary learning feature splitting
- feature split
tags:
- kg/term
- concept
- term
kg:
  id: term:feature-splitting
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[tc2023--towards-monosemanticity]]'
- '[[feature-universality]]'
- '[[monosemanticity]]'
- '[[sparse-autoencoder]]'
relationships:
- type: proposed_by
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
- type: related_to
  target: '[[feature-universality]]'
  target_id: term:feature-universality
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

Feature splitting is the empirical phenomenon whereby a coarse feature learned by a small sparse autoencoder divides into multiple finer, more specific sub-features when a larger autoencoder is trained on the same activations. For example, a single base64 feature in a 512-feature dictionary splits into three distinct base64-context features in a 4,096-feature dictionary and into even more sub-features at 131,072. The observation suggests that SAE dictionaries offer an adjustable resolution for probing the same underlying representational structure, with fidelity increasing monotonically with dictionary size.

**Why it matters here:** Feature splitting implies that the granularity at which a model internally represents concepts is not fixed, which has implications for how confidently we can characterize what a model "knows" or is uncertain about at any given scale of analysis.

**Lineage:** introduced alongside [[monosemanticity]] in [[tc2023--towards-monosemanticity]]; [[feature-universality]] is a companion finding that the features being split are genuinely recurring structures across model seeds.
