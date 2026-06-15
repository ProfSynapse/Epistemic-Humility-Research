---
aliases:
- SFT on Unknown examples drives hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-unknown-examples-drive-hallucination
  type: mechanism
  status: canonical
cause: '[[supervised-finetuning]] on examples outside the model''s [[knowledge-boundary]] (Unknown examples in [[slick]])'
effect: Increased [[hallucination]] on closed-book QA accuracy on pre-existing knowledge, linearly proportional to the Unknown fraction in training data
polarity: increases
related:
- '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
- '[[supervised-finetuning]]'
- '[[knowledge-boundary]]'
- '[[slick]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
  target_id: paper:2405.05904
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
- type: related_to
  target: '[[slick]]'
  target_id: method:slick
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

Training on Unknown examples forces the model to memorize surface-level answer patterns for questions it cannot ground in parametric knowledge, which interferes with accurate retrieval of knowledge it does possess. The finetuning-new-knowledge-hallucinations paper (arXiv:2405.05904) quantifies this as a linear relationship between Unknown fraction and hallucination rate, providing a diagnostic tool for predicting hallucination risk from dataset composition. The effect is distinct from forgetting: the model does not lose knowledge it had, but rather learns to bypass it.
