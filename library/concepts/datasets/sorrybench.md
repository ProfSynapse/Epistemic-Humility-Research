---
aliases:
- SorryBench
- Sorry-Bench
- sorry bench
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:sorrybench
  type: dataset
  status: canonical
area: safety-evaluation
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

SorryBench is a harmful-request refusal benchmark spanning many harm categories and measuring whether a model refuses unsafe prompts. In Faithfulness to Refusal, it is used as a transfer check after CAST-calibrated row masks are applied.

**Why it matters here:** SorryBench helps separate a mask that merely overfits CAST wording from a mask that transfers to broader harmful-request refusal behavior.

**Lineage:** used as an external refusal-transfer benchmark in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
