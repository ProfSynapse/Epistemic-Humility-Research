---
aliases:
- Higher-dimensional refusal cones increase attack success rate up to a plateau
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:higher-dimensional-cones-increase-asr
  type: mechanism
  status: canonical
cause: "Sampling jailbreak attack directions from a multi-dimensional [[refusal-concept-cone]] rather than a single refusal direction"
effect: "[[attack-success-rate]] increases with cone dimensionality but plateaus at dimension 4; best-of-N sampling from the cone outperforms temperature-sampling from a single direction in the low-sample regime"
polarity: increases
related:
- '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
- '[[refusal-concept-cone]]'
- '[[attack-success-rate]]'
- '[[dominant-refusal-direction]]'
relationships:
- type: supported_by
  target: '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
  target_id: paper:2502.17420
  confidence: high
- type: related_to
  target: '[[refusal-concept-cone]]'
  target_id: term:refusal-concept-cone
- type: related_to
  target: '[[attack-success-rate]]'
  target_id: metric:attack-success-rate
- type: related_to
  target: '[[dominant-refusal-direction]]'
  target_id: term:dominant-refusal-direction
---

The refusal mechanism of an LLM is not captured by a single direction but by a cone in the safety residual space; attacks that ablate more of this cone are more successful. The concept-cones paper (arXiv:2502.17420) shows that drawing candidate ablation directions uniformly from the span of the top-k refusal principal components increases the attack success rate monotonically up to k=4 before plateauing. In the low-query budget regime, best-of-N sampling from this cone yields higher attack success rates than temperature-based diversification around a single direction, confirming that geometric coverage of the cone matters more than stochastic variation along a single axis.
