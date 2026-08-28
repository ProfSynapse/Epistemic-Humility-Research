---
aliases:
- Bias-Augmented Consistency Training
- BCT
tags:
- kg/method
- concept
- method
kg:
  id: method:bias-augmented-consistency-training
  type: method
  status: canonical
area: training
related:
- '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
- '[[supervised-finetuning]]'
relationships:
- type: used_by
  target: '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
  target_id: paper:2510.27062
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
---

Bias-Augmented Consistency Training generates a target response from the current model on a clean prompt, then fine-tunes the model to produce that response from an augmented prompt containing an irrelevant cue.

**Why it matters here:** BCT internalizes cue invariance through ordinary token-level training and supplies a behavioral comparison for activation-level objectives.
