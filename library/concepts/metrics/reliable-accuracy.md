---
aliases:
- R-Acc
- Reliable Accuracy (R-Acc)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:reliable-accuracy
  type: metric
  status: canonical
area: metrics
---

Reliable Accuracy (R-Acc) measures the fraction of attempted (non-abstained)
answers that are correct: correct answers divided by the sum of correct and
incorrect answers. It quantifies how trustworthy the model's responses are on
questions it chooses to answer.

**Why it matters here:** R-Acc captures the precision side of abstention quality
and complements [[abstain-accuracy]], which scores the abstain/answer decision
itself; together they distinguish models that are selective-but-accurate from
those that abstain poorly or over-abstain while still giving wrong answers.

**Lineage:** pairs with [[abstain-accuracy]] as one of two core AbstainQA
evaluation axes.
