---
aliases:
- Attention ablation reduces late-MLP erasure
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:attention-ablation-attenuates-downstream-mlp-erasure
  type: mechanism
  status: canonical
cause: "Ablating an attention layer in [[chinchilla-7b]] during a factual-recall prompt"
effect: "The counterbalancing downregulation applied by downstream late-layer [[erasure-mlp|erasure MLPs]] to the max-likelihood-token logit is attenuated, i.e. those MLPs suppress the top prediction less than they would in the intact network"
polarity: decreases
related:
- '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
- '[[erasure-mlp]]'
- '[[hydra-effect]]'
- '[[chinchilla-7b]]'
relationships:
- type: supported_by
  target: '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
  target_id: paper:2307.15771
  confidence: high
- type: related_to
  target: '[[erasure-mlp]]'
  target_id: term:erasure-mlp
  confidence: high
- type: related_to
  target: '[[hydra-effect]]'
  target_id: term:hydra-effect
- type: related_to
  target: '[[chinchilla-7b]]'
  target_id: model:chinchilla-7b
---

Ablating an attention layer in [[chinchilla-7b]] does not only trigger
compensatory [[hydra-effect]] attention behaviour downstream; it also
attenuates the counterbalancing function of downstream [[erasure-mlp|erasure
MLPs]], which normally act to downregulate the max-likelihood token. With the
upstream attention layer removed, these late MLPs suppress the top
prediction less, so part of the network's apparent self-repair comes from
erasure *reduction* rather than only from added attention-layer effect.
