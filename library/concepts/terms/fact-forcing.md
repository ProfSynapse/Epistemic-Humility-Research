---
aliases:
- Fact Forcing
- fact-forcing editing problem
tags:
- kg/term
- concept
- term
kg:
  id: term:fact-forcing
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
- '[[factual-recall-localization]]'
- '[[model-editing]]'
relationships:
- type: proposed_by
  target: '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
  target_id: paper:2301.04213
  confidence: high
- type: related_to
  target: '[[factual-recall-localization]]'
  target_id: term:factual-recall-localization
- type: related_to
  target: '[[model-editing]]'
  target_id: method:model-editing
---

Fact Forcing is an editing-problem variant that reuses the same noised-subject
input that Causal Tracing feeds through the model to compute its localization
signal, then edits the model on that noised input so the edited and localized
computations run over matched input distributions rather than the clean
prompts other editing variants use.

**Why it matters here:** Fact Forcing isolates whether the mismatch between
Causal Tracing and edit success in [[factual-recall-localization]] work is
driven by the input distribution mismatch (clean prompt at edit time vs.
noised prompt at tracing time); it is the one editing-problem variant where
tracing effects gain a small amount of predictive power over edit-layer alone.

**Lineage:** proposed alongside Tracing Reversal, Fact Erasure, and Fact
Amplification as editing-problem variants for stress-testing whether
[[model-editing]] success tracks Causal Tracing localization.
