---
aliases:
- reliability
- rely
- Rely
- LLM Reliability Score (rely)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:llm-reliability-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2403.18349--rlkf-rejection-improves-reliability]]'
- '[[accountability]]'
- '[[abstention-rate]]'
- '[[abstention-recall]]'
relationships:
- type: proposed_by
  target: '[[2403.18349--rlkf-rejection-improves-reliability]]'
  target_id: paper:2403.18349
  confidence: high
- type: derived_from
  target: '[[accountability]]'
  target_id: metric:accountability
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
---

The LLM Reliability Score (rely) is a composite metric that balances a model's
tendency to answer correctly against its tendency to avoid wrong answers. It is
defined as rely = ans_rate * accountability + (1 - ans_rate) * accuracy, where
ans_rate is the fraction of questions the model attempts, accountability measures
non-hallucinated output rate, and accuracy measures correctness on attempted
questions. An error-sensitivity parameter alpha can reweight the components
during sensitivity analysis.

**Why it matters here:** rely captures the over-abstention vs. over-answering
tension at the heart of the locked training-regimen study: a model that refuses everything
maximizes accountability but collapses accuracy, while one that always answers
may hallucinate; rely penalizes both failure modes in a single number.

**Lineage:** derives from [[accountability]], which it uses as a sub-component
alongside raw accuracy to form the composite score.
