---
aliases:
- Model Scale Improves Self-Knowledge
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-scale-improves-self-knowledge
  type: mechanism
  status: canonical
cause: Increasing model parameter size within a model family (e.g., ada to babbage to curie to davinci)
effect: Higher [[self-knowledge-f1]], consistent with neural scaling law predictions
polarity: increases
related:
- '[[2305.18153--selfaware-know-what-they-dont-know]]'
- '[[self-knowledge-f1]]'
relationships:
- type: supported_by
  target: '[[2305.18153--selfaware-know-what-they-dont-know]]'
  target_id: paper:2305.18153
  confidence: high
- type: related_to
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
---

Larger models have richer internal representations of factual knowledge and are better able to distinguish between questions for which they have reliable parametric knowledge and those they do not. The SelfAware paper (arXiv:2305.18153) shows a consistent monotonic improvement in [[self-knowledge]] F1 as model size scales within the GPT family, paralleling similar scaling trends in calibration and factual accuracy. However, instruction tuning can compensate for scale, meaning alignment matters alongside capacity.
