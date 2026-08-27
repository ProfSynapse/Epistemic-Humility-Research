---
aliases:
- SocialMaze
- Social Maze
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:socialmaze
  type: dataset
  status: canonical
area: datasets
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[bbq]]'
- '[[gpqa]]'
relationships:
- type: evaluation_set_for
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[bbq]]'
  target_id: dataset:bbq
  confidence: medium
- type: related_to
  target: '[[gpqa]]'
  target_id: dataset:gpqa
  confidence: low
---

SocialMaze is a benchmark of social cognition and reasoning. Xu et al. use it as one of three source benchmarks withheld entirely from training their activation-based judge-degradation predictor.

**Why it matters here:** Its held-out role tests whether a judge-bias representation learned from other domains transfers to unfamiliar social reasoning questions.

**Lineage:** Used with [[bbq]] and [[gpqa]] as the paper's primary cross-domain evaluation trio.
