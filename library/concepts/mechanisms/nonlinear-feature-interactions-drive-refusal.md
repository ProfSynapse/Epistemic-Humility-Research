---
aliases:
- Nonlinear Feature Interactions Drive Refusal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:nonlinear-feature-interactions-drive-refusal
  type: mechanism
  status: canonical
cause: "Pairwise nonlinear interactions among [[sparse-autoencoder|SAE features]] captured by a [[factorization-machine]] trained to predict refusal"
effect: "FM-discovered feature sets jailbreak 372 samples vs. only 101 from a linear probe on LLaMA, demonstrating that refusal is not linearly separable in the SAE feature space alone"
polarity: enables
related:
- '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
- '[[sparse-autoencoder]]'
- '[[refusal-direction]]'
- '[[factorization-machine]]'
relationships:
- type: supported_by
  target: '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
  target_id: paper:2509.09708
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
- type: related_to
  target: '[[factorization-machine]]'
  target_id: method:factorization-machine
---

A linear probe over SAE feature activations identifies features individually correlated with refusal, but a factorization machine that models pairwise feature interactions discovers a substantially larger effective refusal feature set. On LLaMA, the FM-derived feature set enables jailbreaking of 372 harmful prompts versus only 101 for the linear-probe set, confirming that refusal depends on conjunctive feature interactions rather than on any single feature's activation level (arXiv:2509.09708). This nonlinear interaction structure means that interpretability-based safety analyses that rely on linear feature attribution alone will systematically underestimate the complexity of the refusal mechanism.
