---
aliases:
- functional introspective awareness
- activation introspection
- grounded internal-state self-report
tags:
- kg/term
- concept
- term
kg:
  id: term:introspective-awareness
  type: term
  status: canonical
area: verification
related:
- '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
- '[[2605.26242--can-llms-introspect-reality-check]]'
- '[[concept-injection-introspection-test]]'
- '[[residual-stream]]'
- '[[privileged-access-condition]]'
- '[[second-order-computation-condition]]'
relationships:
- type: proposed_by
  target: '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
  target_id: paper:lindsey-2025-introspection
  confidence: high
- type: measured_by
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
- type: related_to
  target: '[[privileged-access-condition]]'
  target_id: term:privileged-access-condition
  confidence: high
- type: related_to
  target: '[[second-order-computation-condition]]'
  target_id: term:second-order-computation-condition
  confidence: high
---

Introspective awareness is the capacity to describe an internal state accurately, with the report causally grounded in that state and routed internally rather than inferred from sampled outputs. The paper also requires indirect evidence that the model internally registers a metacognitive fact about the state before or while reporting it.

**Why it matters here:** The definition separates a causally grounded internal-state report from a fluent claim that may be copied from training data or inferred from visible output.

**Lineage:** The [[concept-injection-introspection-test]] operationalizes accuracy,
grounding, and internality, while metacognitive representation remains only
indirectly tested. Later work separates the [[privileged-access-condition]] from
the stronger [[second-order-computation-condition]].
