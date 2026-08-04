---
aliases:
- SORRY-Bench
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

SorryBench is a fine-grained safety-refusal benchmark that organizes unsafe requests into a detailed taxonomy of topics and instruction styles, including paraphrases, persuasion techniques, and encodings. It provides a higher-resolution measurement of refusal behavior than single-score safety benchmarks.

**Why it matters here:** It is used alongside XSTest and AdvBench to measure how interventions affect safety behavior across request styles. In Faithfulness to Refusal, it also serves as a transfer check after CAST-calibrated row masks are applied, helping distinguish a mask that transfers from one that merely overfits CAST wording.

**Lineage:** Used as an external refusal-transfer benchmark in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
