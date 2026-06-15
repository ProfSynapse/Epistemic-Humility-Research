---
aliases:
- acnt
- accountability score
- Accountability (acnt)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:accountability
  type: metric
  status: canonical
area: metrics
related:
- '[[2403.18349--rlkf-rejection-improves-reliability]]'
- '[[llm-reliability-score]]'
- '[[abstention-rate]]'
- '[[hallucination]]'
relationships:
- type: proposed_by
  target: '[[2403.18349--rlkf-rejection-improves-reliability]]'
  target_id: paper:2403.18349
  confidence: high
- type: related_to
  target: '[[llm-reliability-score]]'
  target_id: metric:llm-reliability-score
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

Accountability (acnt) is the proportion of model responses that are either
correct or explicit refusals, computed as (N_correct + N_refused) / N_total. It
measures a model's ability to avoid outputting incorrect information by crediting
both right answers and honest abstentions equally, treating hallucinated answers
as the sole failure mode.

**Why it matters here:** accountability separates the cost of hallucination from
the cost of over-refusal, which is essential for evaluating SFT-vs-DPO-vs-KTO
abstention strategies: a method that refuses aggressively can score high on
accountability while scoring poorly on the composite [[llm-reliability-score]].

**Lineage:** a component metric of [[llm-reliability-score]]; related to
[[abstention-rate]] but differs by also crediting correct answers, not only
refusals.
