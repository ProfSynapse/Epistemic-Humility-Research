---
aliases:
- WikiText-2
- WikiText2
- wikitext2
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:wikitext-2
  type: dataset
  status: canonical
area: datasets
related:
- '[[wikitext-103]]'
- '[[perplexity]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: related_to
  target: '[[wikitext-103]]'
  target_id: dataset:wikitext-103
  confidence: high
- type: measures
  target: '[[perplexity]]'
  target_id: metric:perplexity
  confidence: medium
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

WikiText-2 is a smaller Wikipedia-derived language-modeling corpus used for evaluating fluency and perplexity. In Faithfulness to Refusal, it supports the utility guard that row masks should not simply damage the model's general language modeling.

**Why it matters here:** It provides a lightweight language-modeling check alongside behavioral safety metrics, helping distinguish targeted refusal edits from broad degradation.

**Lineage:** related to [[wikitext-103]], the larger WikiText benchmark.
