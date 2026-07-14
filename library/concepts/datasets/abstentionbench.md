---
aliases:
- AbstentionBench benchmark
- abstention benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:abstentionbench
  type: dataset
  status: canonical
area: datasets
related:
- '[[2506.09038--abstentionbench]]'
- '[[abstention]]'
- '[[abstention-recall]]'
- '[[llm-as-judge]]'
relationships:
- type: proposed_by
  target: '[[2506.09038--abstentionbench]]'
  target_id: paper:2506.09038
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
---

AbstentionBench is a large-scale benchmark for evaluating LLM abstention,
aggregating 20 diverse datasets spanning six abstention scenarios: answer
unknown, false premise, stale information, subjective questions, underspecified
context, and underspecified intent. It was introduced by Feng et al. 2025 to
enable systematic cross-dataset comparison of abstention behaviour in frontier
LLMs, using an LLM judge for scalable automated scoring.

**Why it matters here:** AbstentionBench establishes the empirical landscape for
abstention generalisation failure across scenario types, which directly motivates
the locked training-regimen study's hypothesis that SFT, DPO, and KTO may trade off abstention
recall and over-abstention differently depending on the query type.

**Lineage:** proposes [[abstention-recall]] as primary metric; uses [[llm-as-judge]]
for automated scoring; introduced by [[2506.09038--abstentionbench]].
