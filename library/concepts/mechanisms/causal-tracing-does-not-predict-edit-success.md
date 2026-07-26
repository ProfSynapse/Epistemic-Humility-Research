---
aliases:
- Causal Tracing Does Not Predict Edit Success
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:causal-tracing-does-not-predict-edit-success
  type: mechanism
  status: canonical
cause: A model MLP layer's [[activation-patching]] (Causal Tracing) localization effect for a fact
effect: No positive relationship to whether editing that layer with [[rank-one-model-editing]] successfully rewrites the fact; the edit-layer choice itself, not the tracing signal, predicts success (rho=-0.13 on GPT-J/CounterFact; edit layer explains R2=0.947 vs. R2=0.016 for tracing effect)
polarity: prevents
related:
- '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
- '[[activation-patching]]'
- '[[rank-one-model-editing]]'
- '[[factual-recall-localization]]'
relationships:
- type: supported_by
  target: '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
  target_id: paper:2301.04213
  confidence: high
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
- type: related_to
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
- type: related_to
  target: '[[factual-recall-localization]]'
  target_id: term:factual-recall-localization
contradicted-by: []
---

arXiv:2301.04213 finds that [[activation-patching]] (Causal Tracing) localization
effects at a candidate GPT-J MLP layer are not positively correlated with
whether [[rank-one-model-editing]] (ROME) successfully rewrites the fact when
edited at that layer (rho=-0.13, p<1e-3, CounterFact). A regression shows the
categorical choice of edit layer explains 94.7% of variance in rewrite score,
while the tracing effect alone explains only 1.6%, and adding tracing effect to
a layer-only model raises R2 by just 0.001. This dissociation between where a
fact is localized and where it can be successfully edited holds broadly across
editing methods and problem variants, undercutting the assumption that
[[factual-recall-localization]] results should guide [[model-editing]] layer
selection.
