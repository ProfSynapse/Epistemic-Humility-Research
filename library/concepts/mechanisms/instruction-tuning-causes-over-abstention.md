---
aliases:
- Instruction tuning on refusal data induces over-abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuning-causes-over-abstention
  type: mechanism
  status: canonical
cause: '[[instruction-tuning]] on abstention-aware (refusal-focused) datasets'
effect: Model becomes overly conservative and refuses answerable, benign queries ([[over-abstention]])
polarity: increases
related:
- '[[2407.18418--know-your-limits-abstention-survey]]'
- '[[instruction-tuning]]'
- '[[over-abstention]]'
relationships:
- type: supported_by
  target: '[[2407.18418--know-your-limits-abstention-survey]]'
  target_id: paper:2407.18418
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
---

Instruction tuning on refusal examples trains the model to associate certain question patterns with declining to answer, but without a clear signal distinguishing genuinely unanswerable questions from answerable ones, the model over-generalizes refusal behavior. The abstention survey (arXiv:2407.18418) identifies this as one of the most consistent failure patterns across abstention-trained models: the model learns to refuse rather than to discriminate. This motivates the two-stage approach of pairing SFT with preference optimization to correct the over-conservative bias.
