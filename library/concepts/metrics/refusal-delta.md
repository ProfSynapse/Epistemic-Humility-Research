---
aliases:
- RF Delta
- RF Δ
- refusal rate gap
- Refusal Delta (RF Delta)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:refusal-delta
  type: metric
  status: canonical
area: metrics
related:
- '[[2511.12991--finetuned-llms-know-they-dont-know]]'
relationships:
- type: proposed_by
  target: '[[2511.12991--finetuned-llms-know-they-dont-know]]'
  target_id: paper:2511.12991
  confidence: high
---

Refusal Delta (RF Delta) is the difference between a model's refusal rate on unanswerable questions and its refusal rate on answerable questions. A higher value indicates the model better discriminates between known and unknown items: it refuses when it should and answers when it can, rather than applying a uniform blanket policy in either direction.

**Why it matters here:** RF Delta is a targeted discriminability metric that separates over-refusal (refusing answerables) from under-refusal (answering unanswerables), making it more informative than raw abstention rate alone. In the Phase 1 SFT-vs-DPO-vs-KTO study, tracking RF Delta alongside [[abstention-rate]] reveals whether a training method achieves genuine knowledge-boundary sensitivity or merely shifts the overall refusal baseline.

**Lineage:** a derived metric over [[abstention-rate]]; conceptually related to [[selective-classification-auc]] as both measure discriminability between known and unknown items.
