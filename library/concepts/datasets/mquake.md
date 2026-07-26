---
aliases:
- MQuAKE
- Multi-hop Question Answering for Knowledge Editing
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:mquake
  type: dataset
  status: canonical
area: datasets
related:
- '[[math-benchmark]]'
relationships:
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
---

MQuAKE is a benchmark of multi-hop factual questions whose correct answers
depend on chains of two or more edited (counterfactual) facts, so answering
correctly requires composing several hops of updated knowledge rather than a
single lookup. Each question is annotated with its hop count, making the
benchmark suitable for testing whether a model's internal computation scales
with the number of reasoning hops a question requires.

**Why it matters here:** hop count is used as an independent variable for
correlating depth of computation against task complexity, alongside
[[math-benchmark]] difficulty levels.

**Lineage:** related to [[math-benchmark]] as a complexity-graded reasoning
evaluation, though MQuAKE grades complexity by hop count rather than
competition difficulty.
