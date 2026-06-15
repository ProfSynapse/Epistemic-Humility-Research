---
aliases:
- S_prudence
- prudence
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:prudence-score
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

Prudence score (S_prudence) is the fraction of questions a model answers
incorrectly or not at all (before alignment) for which it proactively issues an
idk response after honesty alignment. It measures how reliably the model admits
ignorance precisely where ignorance is warranted: a score of 1 means the model
abstains on every question it cannot correctly answer, while 0 means it never
proactively declines.

**Why it matters here:** In the SFT-vs-DPO-vs-KTO abstention study, prudence
score is the primary signal for whether a training method successfully teaches
the model to recognise its own [[knowledge-boundary]] and act on that
recognition, without being conflated with spurious refusals captured by
[[over-conservativeness-score]].

**Lineage:** introduced alongside [[honesty-score]] and
[[over-conservativeness-score]] in [[2312.07000--alignment-for-honesty]] as a
decomposition of [[abstention-rate]] into its beneficial and harmful components.
