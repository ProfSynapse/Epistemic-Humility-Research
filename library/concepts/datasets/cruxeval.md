---
aliases:
- CruxEval benchmark
- CRUX-Eval
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:cruxeval
  type: dataset
  status: canonical
area: datasets
related:
- '[[2606.05145--distributional-failure-signatures]]'
- '[[gpqa]]'
- '[[gsm8k]]'
- '[[failure-recoverability-structure]]'
relationships:
- type: proposed_by
  target: '[[2606.05145--distributional-failure-signatures]]'
  target_id: paper:2606.05145
  confidence: high
- type: related_to
  target: '[[gpqa]]'
  target_id: dataset:gpqa
  confidence: medium
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
- type: related_to
  target: '[[failure-recoverability-structure]]'
  target_id: term:failure-recoverability-structure
  confidence: medium
---

A benchmark of code reasoning problems requiring input/output prediction over Python functions, used to evaluate reasoning capabilities of language models under verifiable-reward settings.

**Why it matters here:** Used in 2606.05145 as one of three verifiable-reward reasoning benchmarks (alongside GPQA and GSM8K) for characterizing failure recoverability structure; provides code-reasoning coverage in the evaluation suite.

**Lineage:** Pre-existing benchmark; introduced prior to 2606.05145; added here because it was absent from the library dataset index.
