---
aliases:
- Fact Forcing Noised Input Boosts Tracing-Edit Correlation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fact-forcing-noised-input-boosts-tracing-edit-correlation
  type: mechanism
  status: canonical
cause: Editing on the same noised-subject input that [[activation-patching]] (Causal Tracing) uses to compute its localization signal, as in the [[fact-forcing]] editing-problem variant
effect: A small but statistically significant increase in how much of edit-success variance the tracing effect explains beyond edit-layer alone (~3% vs. ~1.5% for other variants, p<1e-4 by F-test), for finetuning-based editors
polarity: increases
related:
- '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
- '[[fact-forcing]]'
- '[[causal-tracing-does-not-predict-edit-success]]'
- '[[activation-patching]]'
relationships:
- type: supported_by
  target: '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
  target_id: paper:2301.04213
  confidence: medium
- type: related_to
  target: '[[fact-forcing]]'
  target_id: term:fact-forcing
- type: related_to
  target: '[[causal-tracing-does-not-predict-edit-success]]'
  target_id: mechanism:causal-tracing-does-not-predict-edit-success
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
contradicted-by: []
---

arXiv:2301.04213 reports the one condition under which Causal Tracing's
localization signal gains meaningful predictive power over edit success: the
[[fact-forcing]] editing-problem variant, which edits on the same noised-subject
input Causal Tracing itself uses to compute localization. For
finetuning-based editors, tracing effect explains an additional ~3% of variance
in rewrite score in this setting (up from ~1.5% in the other three editing-problem
variants), significant at p<1e-4 by F-test. This points to the clean-vs-noised
input mismatch, rather than tracing being uninformative in principle, as a
driver of the broader dissociation captured in
[[causal-tracing-does-not-predict-edit-success]].
