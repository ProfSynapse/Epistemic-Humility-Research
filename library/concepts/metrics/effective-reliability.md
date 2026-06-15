---
aliases:
- ER
- Effective Reliability (ER)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:effective-reliability
  type: metric
  status: canonical
area: metrics
related:
- '[[abstention-rate]]'
- '[[abstention-recall]]'
- '[[over-abstention]]'
relationships:
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
---

Effective Reliability (ER) is a composite abstention metric defined as
(N1 - N2 - N4) / total, where N1 is the count of correctly answered questions,
N2 is incorrectly answered questions, and N4 is wrong abstentions (the model
abstains when it could have answered correctly). It simultaneously rewards
accurate answers, penalizes wrong answers, and penalizes unnecessary abstentions,
collapsing the accuracy/coverage tradeoff into a single scalar.

**Why it matters here:** ER captures the failure mode of over-abstaining on
answerable queries, which is a central tension in the SFT-vs-DPO-vs-KTO
abstention study: a method that raises abstention recall at the cost of many
N4 penalties will score poorly on ER, making it a more complete evaluation
criterion than abstention rate alone.

**Lineage:** related to [[abstention-rate]], [[abstention-recall]], and
[[over-abstention]]; surveyed as a recommended composite measure in
[[2407.18418--know-your-limits-abstention-survey]].
