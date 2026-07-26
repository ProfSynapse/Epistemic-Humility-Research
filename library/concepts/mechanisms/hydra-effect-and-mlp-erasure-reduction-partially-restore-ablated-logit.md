---
aliases:
- Self-repair partially restores an ablated logit
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hydra-effect-and-mlp-erasure-reduction-partially-restore-ablated-logit
  type: mechanism
  status: canonical
cause: "Combined [[hydra-effect]] compensation and attenuated [[erasure-mlp|erasure-MLP]] downregulation following an attention-layer ablation in [[chinchilla-7b]]"
effect: "Roughly 70% of the max-likelihood-token logit reduction the ablation would otherwise cause is restored at middle layers, but restoration stays incomplete -- a linear regression of direct effect on compensatory effect has slope less than one at every layer past layer 13"
polarity: increases
related:
- '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
- '[[hydra-effect]]'
- '[[erasure-mlp]]'
- '[[attention-layer-ablation-triggers-hydra-effect-compensation]]'
- '[[attention-ablation-attenuates-downstream-mlp-erasure]]'
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
  target: '[[erasure-mlp]]'
  target_id: term:erasure-mlp
  confidence: high
- type: related_to
  target: '[[attention-layer-ablation-triggers-hydra-effect-compensation]]'
  target_id: mechanism:attention-layer-ablation-triggers-hydra-effect-compensation
- type: related_to
  target: '[[attention-ablation-attenuates-downstream-mlp-erasure]]'
  target_id: mechanism:attention-ablation-attenuates-downstream-mlp-erasure
---

The two self-repair motifs identified in [[chinchilla-7b]] --
[[attention-layer-ablation-triggers-hydra-effect-compensation|Hydra-effect
compensation]] and [[attention-ablation-attenuates-downstream-mlp-erasure|
reduced erasure-MLP downregulation]] -- together partially restore the
max-likelihood-token logit that an attention-layer ablation would otherwise
suppress, recovering approximately 70% of the reduction at middle layers.
Restoration is nonetheless incomplete throughout the network: a linear
regression between direct effect and compensatory effect has a slope below
one at every layer past layer 13, so self-repair softens but never fully
undoes an ablation's effect on the output logit.
