---
aliases:
- DPO corrects over-abstention introduced by instruction tuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-reduces-over-abstention
  type: mechanism
  status: canonical
cause: '[[direct-preference-optimization]] applied after refusal-aware [[instruction-tuning]]'
effect: Reduced [[over-abstention]] while preserving appropriate refusal of unknown questions
polarity: decreases
related:
- '[[2407.18418--know-your-limits-abstention-survey]]'
- '[[direct-preference-optimization]]'
- '[[instruction-tuning]]'
- '[[over-abstention]]'
relationships:
- type: supported_by
  target: '[[2407.18418--know-your-limits-abstention-survey]]'
  target_id: paper:2407.18418
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
---

DPO provides the contrastive signal that instruction tuning lacks: by pairing (question, answer) as preferred against (question, refusal) for answerable questions, it trains the model to discriminate rather than default to refusal. The abstention survey (arXiv:2407.18418) reviews multiple works finding that DPO applied after SFT reliably reduces over-abstention rates while maintaining appropriate refusal on genuinely unknown questions. This two-stage SFT + DPO pattern is now a standard recommendation for abstention training.
