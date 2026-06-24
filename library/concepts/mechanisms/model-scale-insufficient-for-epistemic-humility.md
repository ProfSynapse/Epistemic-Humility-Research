---
aliases:
- Model Scale Insufficient for Epistemic Humility
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-scale-insufficient-for-epistemic-humility
  type: mechanism
  status: canonical
cause: Increasing parameter count without targeted training for uncertainty handling and answer rejection
effect: No reliable improvement in epistemic humility; smaller, better-designed models match or beat much larger ones at selecting "None of the above"
polarity: neutral
related:
- '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
- '[[epistemic-humility]]'
- '[[multimodal-large-language-model]]'
relationships:
- type: supported_by
  target: '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
  target_id: paper:2509.09658
  confidence: medium
- type: related_to
  target: '[[epistemic-humility]]'
  target_id: term:epistemic-humility
- type: related_to
  target: '[[multimodal-large-language-model]]'
  target_id: term:multimodal-large-language-model
---

On HumbleBench (arXiv:2509.09658), parameter count does not predict epistemic
humility: a 4B Visionary-R1 outperforms several substantially larger reasoning
models, and a 5B Phi-4 surpasses a 12B Pixtral among general-purpose models. The
benchmark's authors conclude that robustness to plausible-but-wrong options and
NOTA items is governed by training and adaptation choices rather than scale,
echoing the text-only finding that scaling does little for abstention. This
positions targeted training, not larger models, as the lever for improving
answer rejection. Polarity is marked neutral because added scale neither reliably
helps nor reliably hurts; it is simply not the controlling factor.
