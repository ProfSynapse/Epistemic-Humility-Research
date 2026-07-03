---
aliases:
- Score representation encodes concepts as linear subspaces
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:score-rep-subspace-encodes-concept
  type: mechanism
  status: canonical
cause: "Training a score-based generative model on data whose high-level concepts are [[causal-separability|causally separable]] factors in the data-generating process"
effect: "The centred [[score-representation]] organises each concept's information into a low-dimensional linear subspace identifiable from a small number of contrastive conditioning prompts"
polarity: enables
related:
- '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
- '[[score-representation]]'
- '[[causal-separability]]'
- '[[concepts-as-subspaces]]'
- '[[concept-algebra]]'
relationships:
- type: supported_by
  target: '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
  target_id: paper:2302.03693
  confidence: high
- type: related_to
  target: '[[score-representation]]'
  target_id: method:score-representation
- type: related_to
  target: '[[causal-separability]]'
  target_id: term:causal-separability
- type: related_to
  target: '[[concepts-as-subspaces]]'
  target_id: term:concepts-as-subspaces
---

The centred score representation (conditional score minus unconditional score) of a diffusion model is a linear function of the log-likelihood ratio under the conditioning prompt, which concentrates concept-specific information in a low-dimensional subspace when concepts are causally separable. Contrastive conditioning pairs (e.g., "a man" vs "a woman") suffice to estimate the concept's subspace direction from a small number of samples (arXiv:2302.03693). This [[concepts-as-subspaces]] structure in the score space is what makes concept algebra operations (addition, subtraction, projection) geometrically valid and empirically effective in [[stable-diffusion]].
