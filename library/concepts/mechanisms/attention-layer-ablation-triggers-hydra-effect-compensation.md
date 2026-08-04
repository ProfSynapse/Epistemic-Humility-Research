---
aliases:
- Attention ablation triggers the Hydra effect
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:attention-layer-ablation-triggers-hydra-effect-compensation
  type: mechanism
  status: canonical
cause: "Ablating a single attention layer in [[chinchilla-7b]] during a factual-recall prompt"
effect: "A downstream attention layer -- typically the next layer -- substantially increases its own direct effect on the max-likelihood-token logit, partially compensating for the ablation (the [[hydra-effect]])"
polarity: increases
related:
- '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
- '[[hydra-effect]]'
- '[[chinchilla-7b]]'
- '[[counterfact]]'
relationships:
- type: supported_by
  target: '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
  target_id: paper:2307.15771
  confidence: high
- type: related_to
  target: '[[hydra-effect]]'
  target_id: term:hydra-effect
  confidence: high
- type: related_to
  target: '[[chinchilla-7b]]'
  target_id: model:chinchilla-7b
- type: related_to
  target: '[[counterfact]]'
  target_id: dataset:counterfact
---

Ablating one attention layer of [[chinchilla-7b]] does not simply remove that
layer's contribution to the output logit: it causes another attention layer,
typically the immediately following one, to substantially increase its own
direct effect on the max-likelihood-token logit. This compensatory response
is the [[hydra-effect]], demonstrated on [[counterfact]] factual-recall
prompts via [[causal-effect-decomposition]] of direct vs. indirect layer
effects.
