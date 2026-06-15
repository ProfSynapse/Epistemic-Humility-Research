---
aliases:
- SFT abstention training overfits to in-domain
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-abstention-overfits-indomain
  type: mechanism
  status: canonical
cause: '[[supervised-finetuning]] on rejection examples from in-domain arithmetic questions'
effect: Model becomes over-conservative on out-of-domain tasks ([[gsm8k]]), refusing almost all questions and collapsing OOD [[llm-reliability-score|reliability]] from 35.2 to 20.8
polarity: decreases
related:
- '[[2403.18349--rlkf-rejection-improves-reliability]]'
- '[[supervised-finetuning]]'
- '[[gsm8k]]'
- '[[llm-reliability-score]]'
relationships:
- type: supported_by
  target: '[[2403.18349--rlkf-rejection-improves-reliability]]'
  target_id: paper:2403.18349
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
- type: related_to
  target: '[[llm-reliability-score]]'
  target_id: metric:llm-reliability-score
---

SFT on in-domain abstention examples trains the model to associate the surface features of those questions with refusal, producing a brittle policy that generalizes the refusal behavior to superficially similar but answerable OOD questions. The RLKF paper (arXiv:2403.18349) demonstrates this collapse on GSM8K, where a model SFT-trained to abstain on arithmetic outside its training distribution ends up refusing nearly all GSM8K questions, tanking OOD reliability from 35.2 to 20.8. This motivates knowledge-feedback-based training that conditions abstention on model-specific competence rather than domain features.
