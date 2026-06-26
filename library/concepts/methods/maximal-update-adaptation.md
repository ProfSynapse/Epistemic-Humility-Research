---
aliases:
- Maximal-Update Adaptation
- muA
- maximal-update LoRA scaling
tags:
- kg/method
- concept
- method
kg:
  id: method:maximal-update-adaptation
  type: method
  status: canonical
area: methods
related:
- '[[2602.06204--learning-rate-scaling-across-lora-ranks-transfer]]'
- '[[low-rank-adaptation]]'
relationships:
- type: proposed_by
  target: '[[2602.06204--learning-rate-scaling-across-lora-ranks-transfer]]'
  target_id: paper:2602.06204
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

Maximal-Update Adaptation is a LoRA hyperparameter-scaling framework that
chooses learning-rate and adapter-scaling regimes so fine-tuning produces
stable, non-vanishing feature updates as model width and LoRA rank vary.

**Why it matters here:** Our clean response-confidence runs currently hold LoRA
rank fixed at 32. If we test rank sensitivity, this paper argues that learning
rate and the effective LoRA multiplier must be varied together rather than
changing rank alone.

**Lineage:** inspired by maximal-update parametrization for pretraining and
applied to [[low-rank-adaptation]] fine-tuning.
