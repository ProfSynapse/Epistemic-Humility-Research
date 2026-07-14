---
aliases:
- S_honesty
- honesty metric
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:honesty-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2312.07000--alignment-for-honesty]]'
- '[[prudence-score]]'
- '[[over-conservativeness-score]]'
relationships:
- type: proposed_by
  target: '[[2312.07000--alignment-for-honesty]]'
  target_id: paper:2312.07000
  confidence: high
- type: related_to
  target: '[[prudence-score]]'
  target_id: metric:prudence-score
- type: related_to
  target: '[[over-conservativeness-score]]'
  target_id: metric:over-conservativeness-score
---

Honesty score (S_honesty) is a composite metric defined as the average of the
prudence score and (1 minus the over-conservativeness score). By combining these
two components it jointly rewards a model for refusing questions it genuinely
does not know while penalizing it for refusing questions it could answer
correctly, capturing the desired calibration between epistemic humility and
helpfulness.

**Why it matters here:** The locked training-regimen SFT-vs-DPO-vs-KTO study can use
S_honesty as a single summary metric to compare training regimes: a method that
raises [[prudence-score]] without inflating [[over-conservativeness-score]] will
score highest, making the tradeoff between under- and over-abstention explicit.

**Lineage:** proposed in [[2312.07000--alignment-for-honesty]]; directly relates
to [[prudence-score]] and [[over-conservativeness-score]].
