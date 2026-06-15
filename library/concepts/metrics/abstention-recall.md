---
aliases:
- recall of abstention
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:abstention-recall
  type: metric
  status: canonical
area: metrics
related:
- '[[abstention-rate]]'
- '[[effective-reliability]]'
- '[[over-abstention]]'
- '[[abstentionbench]]'
relationships:
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
- type: related_to
  target: '[[effective-reliability]]'
  target_id: metric:effective-reliability
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
- type: related_to
  target: '[[abstentionbench]]'
  target_id: dataset:abstentionbench
---

Abstention recall is the proportion of samples where abstention is the correct
response on which the model actually abstains. It answers the question: given
that a model should refuse, how often does it actually refuse? AbstentionBench
focuses on recall as the primary metric because frontier LLMs show high
abstention precision (when they do abstain they are usually right) but low
recall (they miss many cases where they should abstain), making recall the
binding constraint in practice.

**Why it matters here:** The SFT-vs-DPO-vs-KTO study aims to improve abstention
recall on knowledge-limit queries without inflating [[over-abstention]], so
recall is one of the two primary evaluation axes alongside [[effective-reliability]].

**Lineage:** related to [[abstention-rate]], [[effective-reliability]], and
[[over-abstention]]; used as primary metric in [[abstentionbench]].
