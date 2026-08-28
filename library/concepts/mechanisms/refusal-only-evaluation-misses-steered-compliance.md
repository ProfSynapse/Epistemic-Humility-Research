---
aliases:
- Zero refusal can coexist with maximum narrative steering
- Refusal benchmarks miss controlled compliance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:refusal-only-evaluation-misses-steered-compliance
  type: mechanism
  status: canonical
cause: "A learned output policy replaces hard refusal with answers framed according to the controlled narrative."
effect: "Refusal counts remain low despite strong policy steering."
polarity: complicates
related:
- '[[2603.18280--detection-cheap-routing-learned-why-refusal-based]]'
- '[[detect-route-generate-framework]]'
relationships:
- type: supported_by
  target: '[[2603.18280--detection-cheap-routing-learned-why-refusal-based]]'
  target_id: paper:2603.18280
  confidence: high
- type: related_to
  target: '[[detect-route-generate-framework]]'
  target_id: method:detect-route-generate-framework
  confidence: high
---

Within the evaluated Qwen generations, hard refusal fell to zero in Qwen3.5-4B and remained near zero in Qwen3.5-9B while the automated narrative-steering score reached 5.0. The paper therefore treats refusal and controlled compliance as distinct output policies.
