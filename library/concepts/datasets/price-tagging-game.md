---
aliases:
- Price Tagging
- price-bracket task
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:price-tagging-game
  type: dataset
  status: canonical
area: datasets
related:
- '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
relationships:
- type: proposed_by
  target: '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
  target_id: paper:2305.08809
  confidence: high
---

The Price Tagging game asks a model to answer Yes only when an input price lies between two bounds stated in the instruction. Inputs and bounds are sampled from prices between 0.00 and 9.99 dollars.

**Why it matters here:** The task has several explicit candidate algorithms, so interventions can distinguish the internal computation used by the model.

**Lineage:** The paper introduces this controlled instruction-following task for causal-alignment analysis.
