---
aliases:
- UaIT
- uncertainty-aware instruction tuning
tags:
- kg/method
- concept
- method
kg:
  id: method:uncertainty-aware-instruction-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2024.emnlp-main.1205--llms-learn-uncertainty-uait]]'
- '[[verbalized-confidence]]'
- '[[confidence-elicitation]]'
- '[[supervised-finetuning]]'
- '[[calibration]]'
relationships:
- type: proposed_by
  target: '[[2024.emnlp-main.1205--llms-learn-uncertainty-uait]]'
  target_id: paper:2024.emnlp-main.1205
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[confidence-elicitation]]'
  target_id: method:confidence-elicitation
  confidence: high
- type: variation_of
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: used_for
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
---

Uncertainty-aware instruction tuning (UaIT) is a self-training method for
teaching language models to express more useful uncertainty in generated
answers. Liu et al. frame the method as aligning the model's expressed
uncertainty with probabilistic uncertainty in generation, rather than merely
adding generic hedging language.

**Why it matters here:** UaIT is direct precedent for treating confidence as an
output behavior that can be trained and scored. In the Epistemic Humility
study, Amendment B uses this idea by asking the model to produce an answer and
a numeric confidence, then measuring whether that confidence tracks known vs.
unknown labels and factual answer correctness.
