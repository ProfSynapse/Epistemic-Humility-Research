---
aliases:
- An auxiliary model predicts an LLM's confidence from its generations alone
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:auxiliary-model-predicts-llm-confidence-from-generations-alone
  type: mechanism
  status: canonical
cause: "Finetuning a separate small auxiliary model on the target LLM's input question and generated answer text alone (no logits, sequence likelihoods, or hidden states) to predict clustering-derived confidence targets."
effect: "Calibrated, consistent confidence estimates that detect incorrect answers, achieving the best misprediction AUROC and among the lowest Brier/ECE, applicable identically to white-box and black-box LLMs."
polarity: enables
related:
- '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
- '[[apricot]]'
- '[[surrogate-confidence-estimation]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
  target_id: paper:2403.05973
  confidence: high
- type: related_to
  target: '[[apricot]]'
  target_id: method:apricot
  confidence: high
- type: related_to
  target: '[[surrogate-confidence-estimation]]'
  target_id: method:surrogate-confidence-estimation
  confidence: high
---

Ulmer et al. 2024 show APRICOT, trained only on (question, generated-answer) text,
attains the highest misprediction AUROC in all settings and among the lowest
Brier scores and calibration errors for both Vicuna v1.5 7B (white-box) and
GPT-3.5 (black-box) on TriviaQA and CoQA, with no model internals and negligible
overhead. This is the black-box / external-readout contrast to an internal-state
confidence head.
