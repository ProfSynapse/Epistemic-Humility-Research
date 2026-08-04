---
aliases:
- DeepMind Mathematics Dataset
- Mathematics Dataset (Saxton et al.)
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:deepmind-mathematics-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[math-benchmark]]'
- '[[gsm8k]]'
relationships:
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
---

The DeepMind Mathematics Dataset (Saxton et al., 2019) is a large collection of
synthetically generated mathematics questions spanning arithmetic, algebra,
calculus, comparison, and other modules, with question difficulty controlled
programmatically at generation time. Because problems are generated rather than
curated, the dataset gives fine, controllable gradations of difficulty within
each mathematical topic.

**Why it matters here:** its templated, controllable difficulty makes it a
convenient evaluation split for probing whether a model recruits more
computational depth as problem difficulty increases.

**Lineage:** related to [[math-benchmark]] and [[gsm8k]] as mathematical
reasoning evaluations, differing in that its problems are procedurally
generated with explicit difficulty controls rather than hand-curated.
