---
aliases:
- A refusal circuit can recover behavior under soft patching yet invert toward compliance under hard isolation.
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hard-ablation-can-invert-patch-faithful-refusal-circuits
  type: mechanism
  status: canonical
cause: "A patch-faithful refusal circuit is isolated by zero-ablating all out-of-circuit computation."
effect: "The refusal logit difference can fall below the benign baseline and invert toward compliance."
polarity: enables
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[circuit-faithfulness]]'
- '[[qwen2-5-1-5b]]'
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
  target: '[[qwen2-5-1-5b]]'
  target_id: model:qwen2-5-1-5b
  confidence: high
---

On the paired Qwen2.5 refusal task, the EAP-IG circuit recovers 85.4% of the full-model refusal gap under soft patching but scores -2.61 under hard zero-ablation, with a raw refusal logit difference of -1.55 (Section 11.4; Table 6; Figure 7). The result shows that localization under one counterfactual does not guarantee safe isolation under another.
