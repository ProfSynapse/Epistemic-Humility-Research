---
aliases:
- Detect, Route, Generate
- three-stage alignment framework
- detection-routing-output framework
tags:
- kg/method
- concept
- method
kg:
  id: method:detect-route-generate-framework
  type: method
  status: canonical
area: methods
related:
- '[[2603.18280--detection-cheap-routing-learned-why-refusal-based]]'
- '[[linear-probe]]'
- '[[directional-ablation]]'
relationships:
- type: proposed_by
  target: '[[2603.18280--detection-cheap-routing-learned-why-refusal-based]]'
  target_id: paper:2603.18280
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
---

The detect-route-generate framework separates concept encoding, learned policy routing, and generated output. It treats routing as a functional abstraction inferred when interventions change behavioral responses while concept detection remains intact, not as a directly observed localized module.

**Why it matters here:** The framework distinguishes a readable internal signal from the learned computation that makes generation act on that signal.

**Lineage:** It combines [[linear-probe]] evidence for detection with [[directional-ablation]] and behavioral evaluation for routing and output.
