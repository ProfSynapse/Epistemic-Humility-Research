---
aliases:
- activation patching depends on metric and corruption choices
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:activation-patching-results-depend-on-method-choices
  type: mechanism
  status: canonical
cause: "Choices of patching metric, clean/corrupt prompt construction, and corruption method."
effect: "Activation-patching attribution results can change."
polarity: modulates
related:
- '[[2309.16042--towards-best-practices-of-activation-patching-in-language-models]]'
- '[[activation-patching]]'
- '[[logit-difference]]'
- '[[symmetric-token-replacement]]'
- '[[gaussian-noise-corruption]]'
relationships:
- type: supported_by
  target: '[[2309.16042--towards-best-practices-of-activation-patching-in-language-models]]'
  target_id: paper:2309.16042
  confidence: high
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: high
- type: related_to
  target: '[[logit-difference]]'
  target_id: metric:logit-difference
  confidence: medium
- type: related_to
  target: '[[symmetric-token-replacement]]'
  target_id: method:symmetric-token-replacement
  confidence: medium
- type: related_to
  target: '[[gaussian-noise-corruption]]'
  target_id: method:gaussian-noise-corruption
  confidence: medium
---

Activation-patching findings can depend on metric choice, corruption choice, and
other method details, so mechanism program pilots should predeclare those choices before
interpreting effects.
