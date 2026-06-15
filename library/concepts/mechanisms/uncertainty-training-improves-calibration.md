---
aliases:
- Learning uncertainty during training improves calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:uncertainty-training-improves-calibration
  type: mechanism
  status: canonical
cause: Including uncertainty-labeled examples (with 'I don't know' suffixes) in [[supervised-finetuning]] training
effect: Better-calibrated model that estimates [[calibration|uncertainty]] more accurately than models using uncertainty only at test time
polarity: enables
related:
- '[[2311.09677--r-tuning-say-i-dont-know]]'
- '[[supervised-finetuning]]'
- '[[calibration]]'
relationships:
- type: supported_by
  target: '[[2311.09677--r-tuning-say-i-dont-know]]'
  target_id: paper:2311.09677
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
---

Test-time prompting for uncertainty (e.g., asking the model to hedge) does not change the model's internal probability estimates; only training on uncertainty-labeled examples adjusts the weights to produce calibrated outputs. By exposing the model to explicit "I don't know" responses for out-of-boundary questions during SFT, the model learns to distinguish between questions it can and cannot answer. The R-Tuning paper (arXiv:2311.09677) shows this training-time approach consistently outperforms inference-time uncertainty elicitation on [[triviaqa]] and [[selfaware]] evaluations.
