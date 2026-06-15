---
aliases:
- verbalization
- verbalized probability
- Verb. 1S
- Verb. 2S
- verbalized calibration
- direct confidence elicitation
- vanilla verbalized confidence
- verbalized uncertainty
- uncertainty in words
tags:
- kg/method
- concept
- method
kg:
  id: method:verbalized-confidence
  type: method
  status: canonical
area: methods
related:
- '[[2305.14975--just-ask-for-calibration]]'
- '[[calibration]]'
- '[[confidence-elicitation]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2305.14975--just-ask-for-calibration]]'
  target_id: paper:2305.14975
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
- type: related_to
  target: '[[confidence-elicitation]]'
  target_id: method:confidence-elicitation
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
---

Verbalized confidence is a technique where a language model generates a natural-language expression of its own certainty (for example, "90% confident" or "I am not sure") rather than relying on token log-probabilities. Because verbalized probability is derived from the model's generated text rather than internal logits, it applies to any model that produces natural language output and mirrors the way humans communicate uncertainty.

**Why it matters here:** In the SFT-vs-DPO-vs-KTO abstention study, verbalized confidence is one of the primary signals a model can use to communicate calibrated uncertainty without simply refusing to answer, making it a complement to hard abstention. Whether preference-optimization training (DPO, KTO) preserves or degrades verbalized calibration quality relative to SFT is a question the study can probe using [[expected-calibration-error]] and [[brier-score]].

**Lineage:** proposed in [[2305.14975--just-ask-for-calibration]] and [[2205.14334--teaching-models-uncertainty-in-words]]; related to [[calibration]] and [[confidence-elicitation]]; applied to RLHF-trained models in [[2306.13063--can-llms-express-uncertainty]].
