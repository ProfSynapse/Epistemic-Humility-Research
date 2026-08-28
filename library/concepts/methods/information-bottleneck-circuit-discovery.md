---
aliases:
- IBCircuit
- information-bottleneck circuit discovery
tags:
- kg/method
- concept
- method
kg:
  id: method:information-bottleneck-circuit-discovery
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[circuitkit]]'
- '[[circuit-faithfulness]]'
relationships:
- type: studied_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[circuitkit]]'
  target_id: method:circuitkit
  confidence: high
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
  confidence: high
---

Information-bottleneck circuit discovery learns a soft mask over model components by optimizing task preservation together with a sparsity-promoting information-bottleneck penalty. It runs on clean inputs without requiring a contrastive corrupt counterpart and can produce neuron-level masks.

**Why it matters here:** A clean-only discovery route is valuable when epistemic-humility data lack a defensible counterfactual pairing, but the learned mask still needs causal and matched-baseline evaluation before it is treated as mechanistic.

**Lineage:** IBCircuit is an existing discovery algorithm integrated and empirically compared by [[circuitkit]].
