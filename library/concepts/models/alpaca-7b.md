---
aliases:
- Alpaca 7B
- Alpaca-7B
tags:
- kg/model
- concept
- model
kg:
  id: model:alpaca-7b
  type: model
  status: canonical
area: models
related:
- '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
- '[[alpaca-dataset]]'
relationships:
- type: proposed_by
  target: '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
  target_id: paper:2305.08809
  confidence: medium
- type: related_to
  target: '[[alpaca-dataset]]'
  target_id: dataset:alpaca-dataset
  confidence: high
---

Alpaca-7B is a 7-billion-parameter instruction-tuned LLaMA model. The paper studies its internal computation while it follows a synthetic price-bracket instruction.

**Why it matters here:** It is the paper's 7B test case for scaling causal-alignment search to an instruction-tuned language model.

**Lineage:** Alpaca-7B is instruction-tuned from LLaMA using the Stanford Alpaca data and recipe.
