---
aliases:
- Contrastive Weight Steering
- CWS
- contrastive weight arithmetic
- weight steering
tags:
- kg/method
- concept
- method
kg:
  id: method:contrastive-weight-steering
  type: method
  status: canonical
area: steering
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[activation-steering]]'
- '[[low-rank-adaptation]]'
- '[[weight-steering-vector]]'
relationships:
- type: proposed_by
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
- type: related_to
  target: '[[weight-steering-vector]]'
  target_id: term:weight-steering-vector
  confidence: high
---

Contrastive weight steering isolates a behavioral direction in parameter space by subtracting weights from opposing fine-tunes, then adds a scaled version of that direction to a pretrained or task-fine-tuned model. The paper implements the fine-tunes with LoRA and applies the resulting direction as a post-training weight edit.

**Why it matters here:** The method installs behavioral control in model weights and can be evaluated without an online activation intervention. It does not condition the edit on a model's internal answerability state.

**Lineage:** It adapts task-vector arithmetic to paired positive and negative fine-tunes and contrasts directly with [[activation-steering]].
