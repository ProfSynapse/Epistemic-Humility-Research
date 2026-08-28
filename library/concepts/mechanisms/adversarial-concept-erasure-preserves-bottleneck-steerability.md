---
aliases:
- Removing concept information from unsupervised features prevents bottleneck bypass
- Adversarial disentangling makes concept neurons causally useful for generation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:adversarial-concept-erasure-preserves-bottleneck-steerability
  type: mechanism
  status: canonical
cause: "Adversarial training removes labeled concept information from the unsupervised feature path that runs beside the concept bottleneck."
effect: "Token prediction must rely more on the interpretable concept neurons, making activation interventions substantially more steerable."
polarity: enables
related:
- '[[2412.07992--concept-bottleneck-large-language-models]]'
- '[[concept-bottleneck-large-language-model]]'
- '[[adversarial-debiasing]]'
- '[[steerability]]'
relationships:
- type: supported_by
  target: '[[2412.07992--concept-bottleneck-large-language-models]]'
  target_id: paper:2412.07992
  confidence: high
- type: related_to
  target: '[[concept-bottleneck-large-language-model]]'
  target_id: method:concept-bottleneck-large-language-model
  confidence: high
- type: related_to
  target: '[[adversarial-debiasing]]'
  target_id: method:adversarial-debiasing
  confidence: high
- type: related_to
  target: '[[steerability]]'
  target_id: metric:steerability
  confidence: high
---

Across four generation datasets, the adversarially disentangled CB-LLM reached steerability scores from 0.76 to 0.95. Removing adversarial training reduced the range to 0.21 through 0.69, despite similar concept-detection accuracy.
