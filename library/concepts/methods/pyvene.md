---
aliases:
- pyvene
- Pyvene intervention library
tags:
- kg/method
- concept
- method
kg:
  id: method:pyvene
  type: method
  status: canonical
area: methods
related:
- '[[2403.07809--pyvene-library-understanding-improving-pytorch-models-interventions]]'
- '[[causal-intervention]]'
- '[[activation-patching]]'
relationships:
- type: proposed_by
  target: '[[2403.07809--pyvene-library-understanding-improving-pytorch-models-interventions]]'
  target_id: paper:2403.07809
  confidence: high
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: high
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: high
---

pyvene is an open-source Python library for configuring and applying interventions to PyTorch models. It supports activation replacement, addition, collection, custom and trainable interventions, and multi-source execution in parallel or sequence.

**Why it matters here:** It provides reusable machinery for testing whether a hidden-state variable causally affects generation and for training models under intervention-defined losses.

**Lineage:** The library unifies intervention patterns used in activation patching, causal tracing, distributed alignment search, and interchange intervention training.
