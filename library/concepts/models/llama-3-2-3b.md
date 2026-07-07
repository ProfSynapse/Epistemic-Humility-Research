---
aliases:
- LLaMA-3.2-3B
- Llama-3.2-3B
- Llama 3.2 3B
tags:
- kg/model
- concept
- model
kg:
  id: model:llama-3-2-3b
  type: model
  status: canonical
area: models
related:
- '[[llama3-8b]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: related_to
  target: '[[llama3-8b]]'
  target_id: model:llama3-8b
  confidence: high
- type: studied_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

LLaMA-3.2-3B is a small Meta Llama 3.2 language model. Faithfulness to Refusal uses it in the cross-model selector audit and in the behavior-level comparison of which selectors install refusal most effectively.

**Why it matters here:** It provides a mid-small scale point between LLaMA-3.2-1B and 8B-scale models for checking whether selector behavior is architecture- and scale-dependent.

**Lineage:** member of the Llama 3 family, related to [[llama3-8b]].
