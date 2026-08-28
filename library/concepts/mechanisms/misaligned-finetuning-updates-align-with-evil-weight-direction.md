---
aliases:
- Misaligned fine-tuning updates align with an evil contrastive weight direction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:misaligned-finetuning-updates-align-with-evil-weight-direction
  type: mechanism
  status: canonical
cause: "A model is fine-tuned on narrow bad-advice datasets that produce emergent misalignment."
effect: "Its parameter update has higher cosine similarity with contrastive evil weight directions than good-advice or control updates do."
polarity: increases
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[weight-vector-monitoring]]'
- '[[emergent-misalignment]]'
- '[[cosine-similarity]]'
relationships:
- type: supported_by
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: medium
- type: related_to
  target: '[[weight-vector-monitoring]]'
  target_id: method:weight-vector-monitoring
  confidence: high
- type: related_to
  target: '[[emergent-misalignment]]'
  target_id: term:emergent-misalignment
  confidence: high
- type: related_to
  target: '[[cosine-similarity]]'
  target_id: metric:cosine-similarity
  confidence: high
---

Figures 8 and 9 show that contrastive evil directions are closer to bad-advice fine-tuning updates than to good or control updates, and that evil directions cluster more with each other than with controls. The paper calls this evidence preliminary because similarities are small and the monitoring experiments are narrow.
