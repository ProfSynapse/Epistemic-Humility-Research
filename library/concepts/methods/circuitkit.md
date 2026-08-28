---
aliases:
- CircuitKIT
- Circuit Discovery, Evaluation, and Application Toolkit
tags:
- kg/method
- concept
- method
kg:
  id: method:circuitkit
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[circuitscores-artifact]]'
- '[[multi-pillar-circuit-evaluation]]'
- '[[attribution-patching]]'
- '[[automated-circuit-discovery]]'
relationships:
- type: proposed_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[circuitscores-artifact]]'
  target_id: term:circuitscores-artifact
  confidence: high
- type: related_to
  target: '[[multi-pillar-circuit-evaluation]]'
  target_id: method:multi-pillar-circuit-evaluation
  confidence: high
- type: related_to
  target: '[[attribution-patching]]'
  target_id: method:attribution-patching
  confidence: high
- type: related_to
  target: '[[automated-circuit-discovery]]'
  target_id: method:automated-circuit-discovery
  confidence: high
---

CircuitKIT is a source-available Python toolkit that connects circuit discovery, diagnostic evaluation, downstream intervention, checkpoint export, and benchmark scoring through a common interface. It exposes stateful, functional, and YAML-driven entry points and registers multiple discovery backends and intervention selectors behind one typed artifact contract.

**Why it matters here:** It offers a concrete reference architecture for turning Synaptic Tuner's activation-reading and activation-writing primitives into a reproducible circuit workflow with standardized artifacts, diagnostics, matched controls, and downstream outcome checks.

**Lineage:** Built on TransformerLens and composes existing families including [[attribution-patching]] and [[automated-circuit-discovery]] through the [[circuitscores-artifact]] and [[multi-pillar-circuit-evaluation]].
