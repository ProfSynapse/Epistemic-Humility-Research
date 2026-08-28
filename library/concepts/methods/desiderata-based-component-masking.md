---
aliases:
- Desiderata-based Component Masking
- DCM
tags:
- kg/method
- concept
- method
kg:
  id: method:desiderata-based-component-masking
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[activation-patching]]'
- '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
relationships:
- type: derived_from
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: high
- type: used_by
  target: '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
  target_id: paper:2402.14811
  confidence: high
---

Desiderata-based Component Masking optimizes a sparse binary mask over components using counterfactual input pairs with a specified target output. It identifies sets of components whose patched activations jointly implement a proposed semantic function.
