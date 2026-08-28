---
aliases:
- EAS
- Empirical Activation Similarity
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:empirical-activation-similarity
  type: metric
  status: canonical
area: metrics
related:
- '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
- '[[steering-vector]]'
relationships:
- type: proposed_by
  target: '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
  target_id: paper:2606.00995
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

Empirical Activation Similarity is the cosine similarity between a teacher
steering vector and the mean residual-stream shift induced in a student by
fine-tuning at a given training step. It tracks whether the student's learned
activation change aligns with the teacher's intervention direction.

**Why it matters here:** EAS measures whether a behavior-changing direction is
actually installed during weight training rather than inferred only from
behavior.

**Lineage:** It applies cosine similarity to residual-stream shifts in the
[[steering-vector-distillation]] pipeline.
