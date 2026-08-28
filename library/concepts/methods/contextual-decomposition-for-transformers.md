---
aliases:
- CD-T
- contextual decomposition for transformers
- contextual decomposition circuit discovery
tags:
- kg/method
- concept
- method
kg:
  id: method:contextual-decomposition-for-transformers
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

Contextual decomposition for transformers is a clean-only, gradient-free circuit-discovery method. It propagates relevant and irrelevant activation components through transformer blocks and attributes a prediction to the source components that carry the relevant signal.

**Why it matters here:** CD-T gives Synaptic Tuner a methodologically distinct read path when contrastive data are unavailable, while CircuitKIT's IOI study shows that high behavioral faithfulness can coexist with zero overlap with the canonical attention-head taxonomy.

**Lineage:** CD-T is an existing discovery algorithm integrated and empirically compared by [[circuitkit]].
