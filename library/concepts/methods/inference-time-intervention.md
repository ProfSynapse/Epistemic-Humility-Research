---
aliases:
- Inference-Time Intervention (ITI)
- ITI
tags:
- kg/method
- concept
- method
kg:
  id: method:inference-time-intervention
  type: method
  status: canonical
area: methods
related:
- '[[2306.03341--inference-time-intervention]]'
- '[[mass-mean-probing]]'
- '[[linear-probe]]'
- '[[truth-direction]]'
relationships:
- type: proposed_by
  target: '[[2306.03341--inference-time-intervention]]'
  target_id: paper:2306.03341
  confidence: high
- type: derived_from
  target: '[[mass-mean-probing]]'
  target_id: method:mass-mean-probing
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
---

Inference-Time Intervention (ITI) identifies a sparse set of attention heads
whose activations linearly encode a target property (truthfulness), then shifts
those head outputs along a mass-mean direction at every decoding step, scaling the
shift by a strength parameter alpha times the activation standard deviation along
that direction. The directions are located with only a few hundred labeled
examples and no weight update.

**Why it matters here:** ITI shows model truthfulness can be raised substantially
without training, and gives causal evidence that truth-correlated directions in
attention heads mediate output truthfulness. That makes it a probe of where
epistemic signal lives, and its tunable truthfulness-helpfulness tradeoff is a
steering-time analogue of the over-abstention tax seen in abstention finetuning.

**Lineage:** builds on latent-truth-direction work such as
[[mass-mean-probing]] and [[linear-probe]] for finding the directions, and on
activation-addition steering for applying them. It uses the mass-mean estimator
in preference to the raw probe-weight direction.
