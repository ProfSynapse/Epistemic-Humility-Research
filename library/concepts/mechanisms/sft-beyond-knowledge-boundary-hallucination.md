---
aliases:
- SFT on out-of-knowledge questions drives hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-beyond-knowledge-boundary-hallucination
  type: mechanism
  status: canonical
cause: Standard [[instruction-tuning]] that forces answers on questions outside the model's [[knowledge-boundary]]
effect: Model learns to [[hallucination|hallucinate]] confident-sounding answers rather than refuse, even when wrong
polarity: increases
related:
- '[[2311.09677--r-tuning-say-i-dont-know]]'
- '[[instruction-tuning]]'
- '[[knowledge-boundary]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2311.09677--r-tuning-say-i-dont-know]]'
  target_id: paper:2311.09677
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

When SFT training data includes gold answers for questions the model cannot answer correctly from parametric knowledge, the cross-entropy loss rewards the model for producing those specific tokens regardless of whether the model has relevant knowledge. The model internalizes a policy of generating plausible-sounding text rather than acknowledging uncertainty. The R-Tuning paper (arXiv:2311.09677) identifies this as the primary driver of hallucination and motivates uncertainty-labeled fine-tuning as a corrective.
