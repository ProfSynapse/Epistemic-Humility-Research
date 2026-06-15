---
aliases:
- Verbalized probability generalizes calibration better than logits under distribution shift
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:verbalized-prob-generalizes-logit-overfits-distribution-shift
  type: mechanism
  status: canonical
cause: Finetuning [[gpt-3]] to output [[verbalized-confidence]] using per-task empirical accuracy labels
effect: '[[calibration]] generalizes under distribution shift (better MSE on multi-answer evaluation) compared to logit-based uncertainty, because the model leverages pre-existing latent representations rather than surface logit information'
polarity: enables
related:
- '[[2205.14334--teaching-models-uncertainty-in-words]]'
- '[[gpt-3]]'
- '[[verbalized-confidence]]'
- '[[calibration]]'
relationships:
- type: supported_by
  target: '[[2205.14334--teaching-models-uncertainty-in-words]]'
  target_id: paper:2205.14334
  confidence: high
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
---

Logit-based uncertainty is tightly coupled to the training distribution; when the input distribution shifts, logits miscalibrate because they reflect surface-level token probability patterns rather than deep epistemic state. Verbalized probability is generated via the model's generative capabilities and draws on latent representations that encode epistemic state more robustly. The teaching-models-uncertainty paper (arXiv:2205.14334) demonstrates this by comparing MSE on held-out multi-answer evaluations, where verbalized finetuning shows substantially better generalization than logit-based methods.
