---
aliases:
- A typed circuit artifact lets discovery, evaluation, and intervention vary independently.
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:shared-circuit-artifact-decouples-discovery-evaluation-intervention
  type: mechanism
  status: canonical
cause: "Discovery backends serialize task, model, granularity, configuration, and component scores into one typed circuit artifact."
effect: "Evaluation and intervention modules can consume circuits from different discovery methods without method-specific conversion code."
polarity: enables
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[circuitscores-artifact]]'
- '[[circuitkit]]'
relationships:
- type: supported_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[circuitscores-artifact]]'
  target_id: term:circuitscores-artifact
  confidence: high
- type: related_to
  target: '[[circuitkit]]'
  target_id: method:circuitkit
  confidence: high
---

CircuitKIT's architecture makes the CircuitScores record the boundary between stages. The same serialized record is used by the pipeline, flat API, CLI, diagnostics, visualization, applications, export, and benchmark integration (Sections 3, 8, and 10; Figures 1 and 5).
