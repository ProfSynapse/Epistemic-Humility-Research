---
aliases:
- knowledge attribution method
- integrated-gradient attribution for knowledge neurons
- Knowledge Attribution (Integrated-Gradient Method)
tags:
- kg/method
- concept
- method
kg:
  id: method:knowledge-attribution
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
- '[[integrated-gradients]]'
- '[[knowledge-neurons]]'
relationships:
- type: proposed_by
  target: '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
  target_id: paper:2104.08696
  confidence: high
- type: derived_from
  target: '[[integrated-gradients]]'
  target_id: method:integrated-gradients
---

Knowledge Attribution applies [[integrated-gradients]] to score the contribution of each FFN intermediate neuron to a model's probability of predicting the correct answer in a relational cloze task. Scores are refined by intersecting high-attribution neurons across multiple paraphrase prompts expressing the same fact, so that only neurons consistently activated by the underlying knowledge (rather than surface form) are retained. The result is a ranked list of [[knowledge-neurons]] for each relational fact.

**Why it matters here:** Attributing factual knowledge to specific neurons is a prerequisite for targeted model editing and for understanding how training shapes or disrupts a model's stored knowledge, which connects to questions about hallucination and knowledge boundary.

**Lineage:** derives from [[integrated-gradients]] (Sundararajan et al., 2017); output used by [[knowledge-surgery]] for neuron-level fact editing.
