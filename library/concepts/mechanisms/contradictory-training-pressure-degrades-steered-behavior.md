---
aliases:
- Contradictory training pressure degrades an embedded steering effect
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:contradictory-training-pressure-degrades-steered-behavior
  type: mechanism
  status: canonical
cause: "Fine-tuning data applies optimization pressure against the behavior installed by [[embedded-activation-steering]]."
effect: "The model recovers the opposed baseline behavior even though the embedded weight edit remains present."
polarity: decreases
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[embedded-activation-steering]]'
- '[[steering-behavioral-preservation]]'
relationships:
- type: supported_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[embedded-activation-steering]]'
  target_id: method:embedded-activation-steering
  confidence: high
- type: related_to
  target: '[[steering-behavioral-preservation]]'
  target_id: metric:steering-behavioral-preservation
  confidence: high
---

Refusal ablation lost 64 percent of its effect on average under SFT, whose
training subset contained refusal completions. Brevity amplification and both
RLHF conditions were better preserved when direct opposing signals were weaker.
