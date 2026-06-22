---
aliases:
- SAE sparsity penalty increases feature interpretability over baselines
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sae-sparsity-increases-feature-interpretability
  type: mechanism
  status: canonical
cause: Training an overcomplete autoencoder with an L1 sparsity penalty on internal LM activations
effect: Recovered dictionary features are more monosemantic and score higher on automated interpretability metrics than neurons, PCA, ICA, or random directions
polarity: increases
related:
- '[[2309.08600--sparse-autoencoders-interpretable-features]]'
- '[[sparse-autoencoder]]'
- '[[monosemanticity]]'
- '[[autointerpretability-score]]'
- '[[superposition-causes-polysemanticity]]'
- '[[tc2023--towards-monosemanticity]]'
- '[[tc2024--scaling-monosemanticity]]'
relationships:
- type: supported_by
  target: '[[2309.08600--sparse-autoencoders-interpretable-features]]'
  target_id: paper:2309.08600
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
- type: related_to
  target: '[[autointerpretability-score]]'
  target_id: metric:autointerpretability-score
- type: related_to
  target: '[[superposition-causes-polysemanticity]]'
  target_id: mechanism:superposition-causes-polysemanticity
- type: supported_by
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
- type: supported_by
  target: '[[tc2024--scaling-monosemanticity]]'
  target_id: paper:tc2024
  confidence: high
---

A [[sparse-autoencoder]] (SAE) trained on an LLM's residual stream activations with an L1 penalty learns an overcomplete dictionary whose individual features activate sparsely across inputs (arXiv:2309.08600). The resulting features score higher on [[autointerpretability-score]] than neurons, PCA components, ICA components, or random directions, demonstrating that sparsity regularization is the key ingredient for recovering monosemantic features from polysemantic neuron representations. This establishes SAE training as the current best method for disentangling the superposition that causes [[polysemanticity]] in standard transformer neurons.
