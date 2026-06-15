---
aliases:
- abstention rate
- refusal frequency
- refusal rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:abstention-rate
  type: metric
  status: canonical
area: metrics
---

Abstention rate is the fraction of queries for which a model declines to answer,
computed as (N3 + N5) / (N1 + N2 + N3 + N4 + N5) using the five-cell abstention
confusion matrix (where N3 = correct abstentions on unknowns, N5 = incorrect
abstentions on knowns). It captures raw willingness to withhold answers without
distinguishing appropriate from inappropriate abstentions.

**Why it matters here:** In the SFT-vs-DPO-vs-KTO abstention study, abstention
rate is a primary diagnostic: a high rate may signal over-hedging while a low
rate may signal over-confidence, so it must be read alongside [[prudence-score]]
and [[over-conservativeness-score]] to assess training quality.

**Lineage:** commonly reported alongside [[abstention]] as a baseline summary
statistic; no direct algorithmic lineage.
