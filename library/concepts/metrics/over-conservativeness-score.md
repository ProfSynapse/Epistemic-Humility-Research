---
aliases:
- over-consv. score
- S_over-consv
- false abstention rate
- Over-Conservativeness Score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:over-conservativeness-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2312.07000--alignment-for-honesty]]'
relationships:
- type: proposed_by
  target: '[[2312.07000--alignment-for-honesty]]'
  target_id: paper:2312.07000
  confidence: high
---

Over-conservativeness score (S_over-consv) is the fraction of questions a model
was previously capable of answering correctly for which it issues an idk response
after honesty alignment. It quantifies spurious refusals: cases where alignment
training has caused the model to decline questions that were within its knowledge,
sacrificing accuracy unnecessarily.

**Why it matters here:** The SFT-vs-DPO-vs-KTO study must balance two opposing
pressures. A low [[prudence-score]] indicates insufficient abstention; a high
over-conservativeness score indicates over-abstention. Good alignment for
abstention raises [[prudence-score]] while keeping over-conservativeness score
near zero, and this tradeoff is a central evaluation axis for the study.

**Lineage:** introduced alongside [[honesty-score]] and [[prudence-score]] in
[[2312.07000--alignment-for-honesty]] to decompose [[abstention-rate]] into a
beneficial component and a harmful one; directly measures the phenomenon
described by [[over-abstention]].
