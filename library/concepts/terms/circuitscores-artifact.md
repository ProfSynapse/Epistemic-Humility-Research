---
aliases:
- CircuitScores
- CircuitScores artifact
- typed circuit representation
tags:
- kg/term
- concept
- term
kg:
  id: term:circuitscores-artifact
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[circuitkit]]'
- '[[circuit-faithfulness]]'
relationships:
- type: proposed_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: required_by
  target: '[[circuitkit]]'
  target_id: method:circuitkit
  confidence: high
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
  confidence: high
---

CircuitScores is CircuitKIT's typed, serializable circuit record. It carries the task descriptor, model identifier, discovery algorithm, granularity, per-component attribution scores, and discovery configuration so that evaluation and application modules can consume a circuit without depending on the backend that produced it.

**Why it matters here:** A stable circuit artifact would let Synaptic Tuner separate extraction from causal evaluation and actuation, compare read methods without rewriting applications, and preserve provenance for every intervention.

**Lineage:** Proposed as the shared contract at the center of [[circuitkit]] and used to feed [[circuit-faithfulness]] diagnostics and downstream interventions.
