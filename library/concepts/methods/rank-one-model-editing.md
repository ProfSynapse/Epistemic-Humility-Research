---
aliases:
- ROME
- Rank-One Model Editing
- Rank-One Model Editing (ROME)
- ROME (Rank-One Model Editing)
- rank-one weight editing
- rank-one model edit
- fact insertion
- rome knowledge editing
tags:
- kg/method
- concept
- method
kg:
  id: method:rank-one-model-editing
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2202.05262--rome-locating-editing-factual-associations]]'
- '[[activation-patching]]'
- '[[model-editing]]'
- '[[knowledge-circuits]]'
relationships:
- type: proposed_by
  target: '[[2202.05262--rome-locating-editing-factual-associations]]'
  target_id: paper:2202.05262
  confidence: high
- type: derived_from
  target: '[[activation-patching]]'
  target_id: method:activation-patching
- type: variation_of
  target: '[[model-editing]]'
  target_id: method:model-editing
- type: related_to
  target: '[[knowledge-circuits]]'
  target_id: term:knowledge-circuits
---

Rank-One Model Editing (ROME) treats transformer MLP weight matrices as
associative memories and inserts a new factual association by performing a
single rank-one update to a precisely targeted weight matrix. The update is
computed via a constrained least-squares solve that balances efficacy (the
edited fact is reproduced) against specificity (surrounding facts are
preserved), using causal tracing to identify which layer and module to edit.

**Why it matters here:** ROME demonstrates that factual knowledge is not
diffusely distributed but locally concentrated, which has direct implications
for understanding how model training instills or erodes self-knowledge and
calibrated uncertainty about specific facts.

**Lineage:** derives from [[activation-patching]] for causal localization;
variation of the broader [[model-editing]] family; findings intersect with
[[knowledge-circuits]] on where factual associations reside.
