---
aliases:
- Pre-trained latent representations enable calibration generalization
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pretrained-latent-representations-enable-calibration-generalization
  type: mechanism
  status: canonical
cause: '[[gpt-3]] pre-training encoding features that correlate with epistemic uncertainty over its own answers'
effect: A linear probe on GPT-3 embeddings can predict answer correctness out-of-distribution, and finetuning rapidly unlocks calibrated [[verbalized-confidence]] expression rather than learning new representations
polarity: enables
related:
- '[[2205.14334--teaching-models-uncertainty-in-words]]'
- '[[gpt-3]]'
- '[[verbalized-confidence]]'
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
---

Pretraining on diverse text exposes models to many examples of expressed uncertainty, confidence, and correctness signals, building internal representations that correlate with epistemic state. This means calibration is not a novel capability that must be learned during fine-tuning; it is a latent capability that fine-tuning or ICL surfaces. The teaching-models-uncertainty paper (arXiv:2205.14334) provides evidence through linear probing of GPT-3 embeddings, showing out-of-distribution correctness prediction well above chance from raw pretrained representations alone.
