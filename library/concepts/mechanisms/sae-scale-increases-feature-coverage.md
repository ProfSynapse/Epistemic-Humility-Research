---
aliases:
- SAE scale increases concept coverage
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sae-scale-increases-feature-coverage
  type: mechanism
  status: canonical
cause: Increasing the number of features in a [[sparse-autoencoder]] from 1 million to 34 million
effect: Greater coverage of rare concepts, feature splitting into finer sub-concepts, and lower training loss following a power-law scaling relationship
polarity: increases
related:
- '[[tc2024--scaling-monosemanticity]]'
- '[[sparse-autoencoder]]'
- '[[feature-splitting]]'
- '[[feature-universality]]'
relationships:
- type: supported_by
  target: '[[tc2024--scaling-monosemanticity]]'
  target_id: paper:tc2024
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[feature-splitting]]'
  target_id: term:feature-splitting
---

Templeton et al. (tc2024) scale sparse autoencoders trained on Claude 3 Sonnet from 1M to 34M features and observe that reconstruction loss follows a power law, rare and abstract concepts gain dedicated feature detectors only at larger scales, and coarse features split into progressively finer sub-features. The coverage of human-recognizable concepts -- countries, emotions, scientific terms -- grows systematically with scale, supporting the view that SAE scale is the primary bottleneck for comprehensive mechanistic coverage of large language models.
