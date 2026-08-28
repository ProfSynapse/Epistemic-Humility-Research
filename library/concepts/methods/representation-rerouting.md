---
aliases:
- Representation Rerouting
- RR
- circuit breaking
tags:
- kg/method
- concept
- method
kg:
  id: method:representation-rerouting
  type: method
  status: canonical
area: methods
related:
- '[[2406.04313--improving-alignment-robustness-circuit-breakers]]'
- '[[lorra]]'
- '[[representation-engineering]]'
relationships:
- type: proposed_by
  target: '[[2406.04313--improving-alignment-robustness-circuit-breakers]]'
  target_id: paper:2406.04313
  confidence: high
- type: derived_from
  target: '[[lorra]]'
  target_id: method:lorra
  confidence: high
- type: related_to
  target: '[[representation-engineering]]'
  target_id: method:representation-engineering
  confidence: high
---

Representation Rerouting trains low-rank adapters so targeted harmful-response representations become orthogonal to the frozen model's original representations. A paired retain loss keeps benign representations close to those of the original model.

**Why it matters here:** RR is an example of installing a representation-space control objective into adapter weights while preserving unrelated behavior.

**Lineage:** It applies Low-Rank Representation Adaptation to a circuit-breaking objective and builds on representation engineering and representation misdirection for unlearning.
