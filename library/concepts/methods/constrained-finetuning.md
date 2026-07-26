---
aliases:
- Constrained Finetuning
- FT+L
- constrained fine-tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:constrained-finetuning
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
- '[[supervised-finetuning]]'
- '[[model-editing]]'
relationships:
- type: used_by
  target: '[[2301.04213--does-localization-inform-editing-surprising-differences-causality]]'
  target_id: paper:2301.04213
  confidence: high
- type: variation_of
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[model-editing]]'
  target_id: method:model-editing
---

Constrained finetuning edits a single fact by gradient-descending the target
weight(s) at a chosen layer on the new fact directly, with the weight update
norm-clipped (constrained) to a small ball around the original weights so the
edit stays local instead of drifting into an unconstrained finetune. It is
applied at a chosen MLP layer or a window of layers (e.g. window sizes 1 and 5)
so its edit-layer choice can be varied independently of any localization
signal.

**Why it matters here:** As a finetuning-based editing method (rather than a
closed-form weight solve like [[rank-one-model-editing]] or [[memit]]),
constrained finetuning is used to check whether the disconnect between Causal
Tracing localization and edit success generalizes beyond ROME-style editors.

**Lineage:** a locality-constrained variant of [[supervised-finetuning]]
applied to the [[model-editing]] problem.
