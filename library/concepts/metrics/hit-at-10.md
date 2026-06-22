---
aliases:
- Hit@10
- H@10
- rank <= 10
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:hit-at-10
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[knowledge-circuits]]'
- '[[factual-recall-localization]]'
- '[[knowledge-attribution]]'
relationships:
- type: related_to
  target: '[[knowledge-circuits]]'
  target_id: term:knowledge-circuits
- type: related_to
  target: '[[factual-recall-localization]]'
  target_id: term:factual-recall-localization
- type: related_to
  target: '[[knowledge-attribution]]'
  target_id: method:knowledge-attribution
---

Hit@10 (H@10) is the fraction of knowledge queries for which the correct target
token appears within the top 10 ranked predictions produced by the model. It is
a rank-based retrieval metric that tolerates near-misses: a model that ranks the
correct token anywhere in the top 10 receives credit, making it more lenient than
exact-match accuracy while still demanding that the model plausibly retrieve the
right answer. In mechanistic interpretability work it is used to assess whether
an isolated circuit (e.g., a knowledge circuit) reproduces the full model's
knowledge recall behavior.

**Why it matters here:** Hit@10 provides a coarse signal for whether a
mechanistic component genuinely encodes factual knowledge, which is relevant to
understanding where and how the model's knowledge boundary is stored.

**Lineage:** related to [[knowledge-circuits]] (where H@10 is used to evaluate
circuit isolation), [[factual-recall-localization]] (the experimental task), and
[[knowledge-attribution]] (methods that identify the components receiving credit).
