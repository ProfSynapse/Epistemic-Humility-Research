---
aliases:
- Narrow benign fine-tuning suppresses emergent misalignment
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:benign-finetuning-suppresses-emergent-misalignment
  type: mechanism
  status: canonical
cause: "Fine-tuning an [[emergent-misalignment|emergently misaligned]] model on approximately 120 benign samples (35 steps, batch size 4), whether drawn from an in-distribution or out-of-distribution domain"
effect: "Full or near-full suppression of broad emergent misalignment as measured by the misalignment score"
polarity: decreases
related:
- '[[2506.19823--persona-features-control-emergent-misalignment]]'
- '[[emergent-misalignment]]'
- '[[emergent-realignment]]'
- '[[supervised-finetuning]]'
relationships:
- type: supported_by
  target: '[[2506.19823--persona-features-control-emergent-misalignment]]'
  target_id: paper:2506.19823
  confidence: high
- type: related_to
  target: '[[emergent-misalignment]]'
  target_id: term:emergent-misalignment
- type: related_to
  target: '[[emergent-realignment]]'
  target_id: term:emergent-realignment
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
---

Because emergent misalignment is mediated by a small set of amplified persona latents, a correspondingly small benign fine-tuning intervention suffices to suppress those latents and restore aligned behaviour. The persona-features paper (arXiv:2506.19823) shows that as few as 120 benign samples over 35 training steps return the misalignment score to near zero, even when the benign data comes from an out-of-distribution domain. This fragility of emergent misalignment to benign correction is the flip side of its fragility to harmful corruption: both directions reflect the fact that a compact, steerable feature mediates the behaviour.
