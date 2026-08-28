---
aliases:
- Linear concept detection does not imply a behavioral policy
- Models can encode a concept without routing generation on it
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:concept-detection-decouples-from-behavioral-routing
  type: mechanism
  status: canonical
cause: "A model linearly encodes a topic or concept in hidden activations."
effect: "The model may still lack an active policy that routes generation according to that detected concept."
polarity: decouples
related:
- '[[2603.18280--detection-cheap-routing-learned-why-refusal-based]]'
- '[[detect-route-generate-framework]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[2603.18280--detection-cheap-routing-learned-why-refusal-based]]'
  target_id: paper:2603.18280
  confidence: high
- type: related_to
  target: '[[detect-route-generate-framework]]'
  target_id: method:detect-route-generate-framework
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

All tested models showed high train-set probe separability, including null and permuted-label controls. Category-held-out results varied, and Yi-1.5-9B encoded the political topic without showing the corresponding censorship behavior, supporting a separation between detection and policy routing.
