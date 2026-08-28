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
area: datasets
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[2409.05907--programming-refusal-conditional-activation-steering]]'
relationships:
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
- type: used_by
  target: '[[2409.05907--programming-refusal-conditional-activation-steering]]'
  target_id: paper:2409.05907
  confidence: high
---

SorryBench is a fine-grained safety-refusal benchmark that organizes unsafe
requests into a detailed taxonomy of topics and instruction styles (including
paraphrases, persuasion techniques, and encodings), designed to give
higher-resolution measurement of refusal behavior than single-score safety
benchmarks.

**Why it matters here:** it is used alongside XSTest and AdvBench to give a
finer-grained read on how interventions on massive-activation rigidity affect
safety-alignment behavior across request styles, not just a single refusal
rate.

**Also used by:** in Faithfulness to Refusal, SorryBench is used as a transfer
check after CAST-calibrated row masks are applied, helping separate a mask
that merely overfits CAST wording from a mask that transfers to broader
harmful-request refusal behavior.

In Programming Refusal with Conditional Activation Steering, SorryBench
supplies the harmful prompt taxonomy used to build and evaluate the harmfulness
condition vector.

**Lineage:** used as an external refusal-transfer benchmark in
[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]].
