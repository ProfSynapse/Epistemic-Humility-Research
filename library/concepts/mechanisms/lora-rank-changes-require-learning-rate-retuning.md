---
aliases:
- LoRA rank changes can invalidate learning rate transfer
- LoRA rank and learning rate are coupled
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:lora-rank-changes-require-learning-rate-retuning
  type: mechanism
  status: canonical
cause: "Changing LoRA rank or effective LoRA multiplier without jointly reconsidering the learning rate."
effect: "The stable feature-update regime can shift, so a previously good learning rate may become suboptimal or unstable."
polarity: causes
related:
- '[[2602.06204--learning-rate-scaling-across-lora-ranks-transfer]]'
- '[[low-rank-adaptation]]'
- '[[maximal-update-adaptation]]'
relationships:
- type: supported_by
  target: '[[2602.06204--learning-rate-scaling-across-lora-ranks-transfer]]'
  target_id: paper:2602.06204
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
- type: related_to
  target: '[[maximal-update-adaptation]]'
  target_id: method:maximal-update-adaptation
  confidence: high
---

Chen, Villar, and Hayou identify two LoRA regimes: one where the optimal
learning rate is roughly rank-invariant and another where it decreases with
rank. For this project, rank sweeps should therefore be coupled with an
explicit learning-rate rule or panel.
