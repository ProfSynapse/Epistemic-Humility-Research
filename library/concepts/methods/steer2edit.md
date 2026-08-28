---
aliases:
- Steer2Edit
- activation-steering-guided component editing
- component-level steering edit
tags:
- kg/method
- concept
- method
kg:
  id: method:steer2edit
  type: method
  status: canonical
area: methods
related:
- '[[2602.09870--steer2edit-activation-steering-component-level-editing]]'
- '[[activation-steering]]'
- '[[rank-one-model-editing]]'
relationships:
- type: proposed_by
  target: '[[2602.09870--steer2edit-activation-steering-component-level-editing]]'
  target_id: paper:2602.09870
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: variation_of
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
  confidence: high
---

Steer2Edit is a training-free method that turns contrastive steering vectors into diagnostic signals for rank-1 edits to attention-head output projections and MLP down-projection neurons. It selects component edit magnitudes with alignment scores and an Elastic-Net objective, then folds the resulting updates into model weights so generation uses the standard forward pass.

**Why it matters here:** The method tests whether a representation-space direction can guide persistent, component-selective parameter changes that alter truthfulness, refusal, or reasoning behavior.

**Lineage:** It derives its semantic directions from [[activation-steering]] and applies them through a component-level variant of [[rank-one-model-editing]].
