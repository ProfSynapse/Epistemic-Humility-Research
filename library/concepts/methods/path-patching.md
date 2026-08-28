---
aliases:
- Path Patching
- path-specific activation patching
tags:
- kg/method
- concept
- method
kg:
  id: method:path-patching
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

Path patching replaces activations along selected computational paths with activations from a counterfactual run. The paper ranks candidate attention-head paths by their effect on the correct-token probability and builds an entity-tracking circuit iteratively.
