---
aliases:
- DPO distributed offset bypasses toxic MLP activation regions
- DPO toxicity bypass offset
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-distributed-offset-bypasses-toxic-mlp-activation-regions
  type: mechanism
  status: canonical
cause: "DPO on nontoxic-over-toxic preference pairs makes small parameter changes distributed across GPT-2 Medium's layers."
effect: "The accumulated residual-stream offset reduces entry into MLP key-vector regions that activate toxicity-associated value vectors, while those vectors remain nearly unchanged."
polarity: prevents
related:
- '[[2401.01967--mechanistic-understanding-alignment-algorithms-case-study-dpo]]'
- '[[direct-preference-optimization]]'
- '[[gpt-2-medium]]'
relationships:
- type: supported_by
  target: '[[2401.01967--mechanistic-understanding-alignment-algorithms-case-study-dpo]]'
  target_id: paper:2401.01967
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[gpt-2-medium]]'
  target_id: model:gpt-2-medium
  confidence: high
---

The paper links lower toxic-vector activation to a consistent shift between pre-DPO and post-DPO residual streams. It traces this shift to the accumulated contribution of small changes in many preceding MLP value vectors.
