---
aliases:
- Depth Score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:depth-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
relationships:
- type: proposed_by
  target: '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
  target_id: paper:2505.13898
  confidence: high
---

The Depth Score is a weighted average, over layers, of how causally important
each layer is for the model's future-token predictions (as opposed to only the
current token), giving a single scalar summary of how much of the network's
depth a given input recruits for computation that will be reused later.

**Why it matters here:** [[2505.13898--do-language-models-use-their-depth-efficiently]]
correlates the Depth Score against problem difficulty (MATH levels 1-5) and
reasoning-hop count (MQuAKE) and finds no relationship, arguing that the depth
of computation a model uses is independent of problem complexity.
