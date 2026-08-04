---
aliases:
- MEMIT
- Mass-Editing Memory in a Transformer
tags:
- kg/method
- concept
- method
kg:
  id: method:memit
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
- '[[rank-one-model-editing]]'
- '[[model-editing]]'
relationships:
- type: used_by
  target: '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
  target_id: paper:2301.04213
  confidence: high
- type: derived_from
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
- type: variation_of
  target: '[[model-editing]]'
  target_id: method:model-editing
---

MEMIT (Mass-Editing Memory in a Transformer) extends [[rank-one-model-editing]]
(ROME) from single-fact edits to thousands of simultaneous factual edits by
distributing the associative-memory weight update across a range of
consecutive mid-layer MLP modules rather than a single targeted layer.

**Why it matters here:** MEMIT is one of the editing methods used to test
whether Causal Tracing's localization signal predicts which layer is best to
edit, alongside [[rank-one-model-editing]] and [[constrained-finetuning]].

**Lineage:** derives from [[rank-one-model-editing]]; variation of the broader
[[model-editing]] family.
