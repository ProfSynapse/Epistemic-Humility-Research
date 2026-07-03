---
aliases:
- Representationally independent refusal directions are accessible from the token input via adversarial suffixes
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:repind-directions-are-input-accessible
  type: mechanism
  status: canonical
cause: "GCG adversarial suffix optimisation with an added loss term penalising representation of RepInd-1 in [[residual-stream]] activations"
effect: "Suffixes reduce cosine similarity of RepInd-1 with model activations and achieve 36% jailbreak [[attack-success-rate]], confirming the direction is actively used by the model and not merely latent"
polarity: enables
related:
- '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
- '[[representational-independence]]'
- '[[refusal-direction]]'
- '[[attack-success-rate]]'
relationships:
- type: supported_by
  target: '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
  target_id: paper:2502.17420
  confidence: high
- type: related_to
  target: '[[representational-independence]]'
  target_id: term:representational-independence
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
- type: related_to
  target: '[[attack-success-rate]]'
  target_id: metric:attack-success-rate
---

Non-dominant refusal directions that satisfy representational independence from the dominant direction can nonetheless be targeted from the input by adversarial token suffixes. When GCG optimisation is augmented with a loss term that directly penalises the cosine projection of RepInd-1 onto residual-stream activations, the resulting suffixes suppress that direction and achieve a 36% jailbreak success rate (arXiv:2502.17420). This confirms that representationally independent directions are not merely geometric curiosities but are causally engaged by the model's refusal computation and reachable via input manipulation.
