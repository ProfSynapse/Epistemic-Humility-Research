---
aliases:
- RMSNorm Sharpens Linear Truth Separability
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rms-norm-sharpens-linear-separability
  type: mechanism
  status: canonical
cause: "RMSNorm applied after the attention-weighted average, contracting true-context vectors (which average close to zero due to subject-attribute embedding anticorrelation) to a smaller magnitude than false-context vectors"
effect: "Linear separability of true versus false hidden states emerges post-normalisation; classification accuracy remains at majority-class level before the normalisation is applied"
polarity: enables
related:
- '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
- '[[truth-direction]]'
- '[[linear-representation-hypothesis]]'
relationships:
- type: supported_by
  target: '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
  target_id: paper:2510.15804
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

The geometry of subject and attribute embeddings is such that true subject-attribute pairs have nearly opposite directions in embedding space, causing their attention-weighted average to collapse toward zero. When RMSNorm scales all vectors to unit norm, this collapse amplifies the relative difference between true-context vectors (small pre-norm magnitude) and false-context vectors (larger pre-norm magnitude), producing a magnitude contrast that a linear probe can exploit for classification. The truth-encodings paper (arXiv:2510.15804) demonstrates this by ablating the normalisation step and showing that probe accuracy drops to chance, confirming that RMSNorm is the structural mechanism that renders the truth variable linearly decodable.
