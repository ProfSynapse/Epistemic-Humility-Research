---
aliases:
- Weight-edit reversal fraction
- Steering edit reversal fraction
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:weight-edit-reversal-fraction
  type: metric
  status: canonical
area: metrics
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[vector-recovery-ratio]]'
relationships:
- type: used_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[vector-recovery-ratio]]'
  target_id: metric:vector-recovery-ratio
  confidence: high
---

Weight-edit reversal fraction measures the alignment between a fine-tuning
update and the exact inverse of a prior embedded steering edit. Zero denotes
no linear cancellation and one denotes full cancellation.

**Why it matters here:** It directly tests whether training removes a
weights-level steering intervention rather than compensating elsewhere.

**Lineage:** It complements [[vector-recovery-ratio]] by testing the full
edited weight pattern.
