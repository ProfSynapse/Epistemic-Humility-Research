---
aliases:
- Early injection leaves a computation window for perturbation reports
- Attention routing supports localized perturbation reporting
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:early-layer-perturbations-enable-differential-introspection
  type: mechanism
  status: canonical
cause: "A localized [[steering-vector]] perturbation enters the [[residual-stream]] early enough for attention to route its position and later layers to integrate that signal."
effect: "The model can select the perturbed sentence or compare perturbation strengths above chance, while the same tasks fail for late-layer injections."
polarity: enables
related:
- '[[2512.12411--detecting-disturbance-nuanced-view-introspective-abilities-llms]]'
- '[[sentence-localization-introspection]]'
- '[[strength-comparison-introspection]]'
- '[[activation-steering]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2512.12411--detecting-disturbance-nuanced-view-introspective-abilities-llms]]'
  target_id: paper:2512.12411
  confidence: medium
- type: related_to
  target: '[[sentence-localization-introspection]]'
  target_id: metric:sentence-localization-introspection
  confidence: high
- type: related_to
  target: '[[strength-comparison-introspection]]'
  target_id: metric:strength-comparison-introspection
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

In the five-way attention analysis, all layer-3 heads localize a perturbation
inserted at layer 2. Logit-lens localization develops more slowly and reaches a
plateau only in later layers. The authors infer that early injection leaves
enough downstream computation for a routed anomaly signal to become an explicit
relative prediction. The analyses track the proposed stages but do not ablate
attention routing, so the mechanistic claim remains medium-confidence.
