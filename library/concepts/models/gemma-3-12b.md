---
aliases:
- Gemma-3-12B
- Gemma 3 12B
tags:
- kg/model
- concept
- model
kg:
  id: model:gemma-3-12b
  type: model
  status: canonical
area: models
related:
- '[[gemma-4]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: medium
- type: studied_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

Gemma-3-12B is a 12-billion-parameter model from Google's Gemma 3 family. Faithfulness to Refusal includes it in the language-model-level selector audit to test whether attribution-selector behavior generalizes beyond Llama and Qwen architectures.

**Why it matters here:** The Gemma result broadens the selector-faithfulness claim beyond one model family and helps flag architecture dependence in causal interpretability audits.

**Lineage:** related to the Gemma family atom [[gemma-4]] in this vault.
