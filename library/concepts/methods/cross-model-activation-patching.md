---
aliases:
- Cross-Model Activation Patching
- CMAP
tags:
- kg/method
- concept
- method
kg:
  id: method:cross-model-activation-patching
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[activation-patching]]'
- '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
relationships:
- type: proposed_by
  target: '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
  target_id: paper:2402.14811
  confidence: high
- type: derived_from
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: high
---

Cross-model activation patching replaces a component's activation in one model with the corresponding activation from another model on the same input. It localizes which shared sub-mechanism accounts for a performance difference between architecture-compatible models.
