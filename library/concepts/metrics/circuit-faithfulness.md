---
aliases:
- faithfulness score
- normalized circuit performance
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:circuit-faithfulness
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[sparse-feature-circuits]]'
- '[[attribution-patching]]'
- '[[indirect-object-identification]]'
relationships:
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
- type: related_to
  target: '[[attribution-patching]]'
  target_id: method:attribution-patching
---

Circuit faithfulness is the normalized proportion of full-model performance that
a discovered circuit retains when all non-circuit nodes are mean-ablated, defined
as: faithfulness = (m(C) - m(empty)) / (m(M) - m(empty)), where m(C) is circuit
performance, m(M) is full-model performance, and m(empty) is performance with
all components ablated. An ideal circuit scores 1.0; complement faithfulness
(performance with the circuit deleted) ideally reaches 0, confirming the circuit
is both sufficient and necessary for the behavior.

**Why it matters here:** Circuit faithfulness quantifies how completely a
proposed mechanistic explanation accounts for a target behavior, which is
essential for evaluating whether a hypothesized epistemic-humility circuit
actually drives abstention or uncertainty signaling rather than co-occurring
incidentally.

**Lineage:** operationally paired with [[sparse-feature-circuits]] and
[[attribution-patching]]; benchmark values first established on
[[indirect-object-identification]].
