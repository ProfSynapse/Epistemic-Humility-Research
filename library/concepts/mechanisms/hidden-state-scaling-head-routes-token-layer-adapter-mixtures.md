---
aliases:
- Hidden-state scaling head routes token-layer adapter mixtures
- X-LoRA dynamically mixes experts from hidden states
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hidden-state-scaling-head-routes-token-layer-adapter-mixtures
  type: mechanism
  status: canonical
cause: "An X-LoRA scaling head reads base-model hidden states and predicts softmax-normalized coefficients for each token, layer, and adapter."
effect: "Frozen LoRA experts contribute in input-dependent mixtures that change across tasks and generation stages."
polarity: enables
related:
- '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
- '[[x-lora]]'
- '[[x-lora-scaling-head]]'
- '[[low-rank-adaptation]]'
relationships:
- type: supported_by
  target: '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
  target_id: paper:2402.07148
  confidence: high
- type: related_to
  target: '[[x-lora]]'
  target_id: method:x-lora
  confidence: high
- type: related_to
  target: '[[x-lora-scaling-head]]'
  target_id: term:x-lora-scaling-head
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

The paper's scaling visualizations show sparse, task-dependent mixtures that vary across layers and tokens. The reported benchmark gains establish usefulness of the full architecture but do not independently identify which routing choices are necessary.
