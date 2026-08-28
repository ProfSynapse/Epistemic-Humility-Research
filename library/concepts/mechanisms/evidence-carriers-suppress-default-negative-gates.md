---
aliases:
- Evidence-carrier to default-no gate circuit
- Distributed anomaly features suppress negative-response gates
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:evidence-carriers-suppress-default-negative-gates
  type: mechanism
  status: canonical
cause: "A [[steering-vector]] injection activates many weak evidence-carrier features in early post-injection layers."
effect: "The carriers suppress a compact set of later MLP gate features that promote a default negative answer, enabling an explicit injection-detection report."
polarity: enables
related:
- '[[2603.21396--mechanisms-introspective-awareness]]'
- '[[steering-attribution]]'
- '[[sparse-feature-circuits]]'
- '[[activation-patching]]'
- '[[residual-stream]]'
- '[[generic-irregularity-detection-mimics-steering-awareness]]'
relationships:
- type: supported_by
  target: '[[2603.21396--mechanisms-introspective-awareness]]'
  target_id: paper:2603.21396
  confidence: high
- type: related_to
  target: '[[steering-attribution]]'
  target_id: method:steering-attribution
  confidence: high
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
  confidence: high
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
- type: related_to
  target: '[[generic-irregularity-detection-mimics-steering-awareness]]'
  target_id: mechanism:generic-irregularity-detection-mimics-steering-awareness
  confidence: medium
---

The early carrier population is large, distributed, and partly
concept-specific. Its members increase monotonically with steering strength and
collectively suppress later gate features. Gate ablation removes detection,
gate patching partially restores it on controls, and carrier ablation increases
gate activation. The circuit implements anomaly-sensitive reporting, but the
paper does not test whether a prompt-only semantic irregularity can recruit the
same path.
