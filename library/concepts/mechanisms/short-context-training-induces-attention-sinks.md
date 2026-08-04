---
aliases:
- short-context training induces attention sinks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:short-context-training-induces-attention-sinks
  type: mechanism
  status: canonical
cause: "training loss is dominated by short-range next-token prediction rather than restricted to long-range-only sequence positions."
effect: "attention sinks emerge as a byproduct that supports short-range dependency prediction within a globally-attending mechanism; restricting the loss to long-range-only positions collapses the sink ratio from about 46% down to 1.2-13.0%."
polarity: causes
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
- '[[attention-sink]]'
relationships:
- type: supported_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
---

Sun et al. show attention sinks are induced by short-context training rather
than being an inherent property of attention: restricting the training loss to
long-range-only sequence positions collapses the sink ratio from about 46% down
to 1.2-13.0%. This indicates sinks primarily support short-range dependency
prediction within a globally-attending mechanism (Table 8; Section 4.3.3).
