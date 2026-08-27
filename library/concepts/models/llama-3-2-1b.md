---
aliases:
- LLaMA-3.2-1B
- Llama-3.2-1B
- Llama 3.2 1B
tags:
- kg/model
- concept
- model
kg:
  id: model:llama-3-2-1b
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

LLaMA-3.2-1B is a small Meta Llama 3.2 language model. In Faithfulness to Refusal, it is one of the base models used in the language-model-level neuron selector audit and one of the instruction-tuned models used in behavior-level refusal editing.

**Why it matters here:** The small model tests whether selector faithfulness and refusal-edit behavior are artifacts of 8B-scale models or persist at lower scale.

**Lineage:** member of the Llama 3 family, related to [[llama3-8b]].
