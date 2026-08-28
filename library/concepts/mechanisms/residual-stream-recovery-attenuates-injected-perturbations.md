---
aliases:
- Residual recovery washes out activation injections
- Later layers attenuate injected directions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:residual-stream-recovery-attenuates-injected-perturbations
  type: mechanism
  status: canonical
cause: "Normal downstream computation follows a localized [[steering-vector]] injection into the [[residual-stream]]."
effect: "The perturbed trajectory returns toward its baseline trajectory and loses projection on the injected direction, limiting late explicit reports of the perturbation."
polarity: decreases
related:
- '[[2512.12411--detecting-disturbance-nuanced-view-introspective-abilities-llms]]'
- '[[early-layer-perturbations-enable-differential-introspection]]'
- '[[activation-steering]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2512.12411--detecting-disturbance-nuanced-view-introspective-abilities-llms]]'
  target_id: paper:2512.12411
  confidence: medium
- type: related_to
  target: '[[early-layer-perturbations-enable-differential-introspection]]'
  target_id: mechanism:early-layer-perturbations-enable-differential-introspection
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

Across layers after an injection, perturbed and baseline residual streams become
more similar while the perturbation's projection onto the injected direction
decays. The paper combines this recovery pattern with the late-layer failure of
relative introspection tasks. Because it does not intervene on the recovery
dynamics, the proposed contribution to task failure remains a mechanistic
interpretation rather than a direct causal isolation.
