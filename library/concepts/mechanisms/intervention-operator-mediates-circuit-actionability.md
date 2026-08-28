---
aliases:
- The value of a circuit ranking depends on the downstream intervention that consumes it.
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:intervention-operator-mediates-circuit-actionability
  type: mechanism
  status: canonical
cause: "The same family of circuit-derived component rankings is consumed by pruning, mixed-precision quantization, or fixed-budget fine-tuning."
effect: "Intrinsic faithfulness relates differently to downstream performance because each intervention exposes ranking error through a different operator."
polarity: mediates
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[circuit-faithfulness]]'
- '[[circuitkit]]'
relationships:
- type: supported_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
  confidence: high
- type: related_to
  target: '[[circuitkit]]'
  target_id: method:circuitkit
  confidence: high
---

The intervention studies show three different relationships to the same selector signal. Patch faithfulness anti-correlates with pruning retention in the highlighted BoolQ cell, ablation faithfulness predicts quantization retention, and circuit mask identity does not beat a random equal-budget mask in selective fine-tuning (Sections 11.5 to 11.8; Tables 7 to 9; Figure 8).
