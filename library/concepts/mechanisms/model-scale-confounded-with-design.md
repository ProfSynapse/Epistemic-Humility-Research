---
aliases:
- Model Scale Confounded With Design
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-scale-confounded-with-design
  type: mechanism
  status: canonical
cause: Comparing MLLMs that differ simultaneously in parameter count, architecture, training data, visual encoder, and post-training strategy
effect: Parameter count alone does not explain false-option-rejection rankings; smaller, better-designed models match or beat larger ones, so scale cannot be isolated as the driver
polarity: neutral
related:
- '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
- '[[false-option-rejection]]'
- '[[multimodal-large-language-model]]'
relationships:
- type: supported_by
  target: '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
  target_id: paper:2509.09658
  confidence: high
- type: related_to
  target: '[[false-option-rejection]]'
  target_id: term:false-option-rejection
- type: related_to
  target: '[[multimodal-large-language-model]]'
  target_id: term:multimodal-large-language-model
---

On HumbleBench (arXiv:2509.09658) parameter count does not predict false-option
rejection: a 4B Visionary-R1 outperforms several substantially larger reasoning
models, and a 5B Phi-4 (67.28%) surpasses a 12B Pixtral (66.63%). The authors are
explicit that this is not a controlled scaling-law study, because model size is
confounded with architecture, training data, visual encoders, and post-training
strategy. The takeaway is therefore deliberately cautious: rather than "scale
helps" or "scale hurts", model size is one entangled factor among many, and
design, data quality, and post-training methodology matter at least as much.
Polarity is neutral because added scale neither reliably helps nor reliably hurts
in this comparison; it is simply not isolable as the controlling factor.
