---
aliases:
- Contrastive weight directions generalize behavior control beyond their narrow training domain
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:contrastive-weight-directions-generalize-behavior-control-beyond-training-domain
  type: mechanism
  status: canonical
cause: "A scaled behavioral direction from opposing positive and negative fine-tunes is added to model weights with contrastive weight steering."
effect: "Behavior changes on out-of-distribution factual, arithmetic, and multiple-choice evaluations before comparable general-capability degradation."
polarity: enables
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[contrastive-weight-steering]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: related_to
  target: '[[contrastive-weight-steering]]'
  target_id: method:contrastive-weight-steering
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

Figures 2, 3, and 5 report broader or stronger behavioral control from contrastive weight steering than from the tested activation-steering baseline. The evidence covers sycophancy and evil-answer behavior on evaluations that differ from the vector-construction prompts, but the paper evaluates only controlled tasks and one activation-steering approach.
