---
aliases:
- calibration-error bounds generation error
- delta-coupling hallucination floor
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:cross-entropy-calibration-couples-to-hallucination
  type: mechanism
  status: canonical
cause: "Cross-entropy pretraining minimization drives calibration deviation delta toward zero"
effect: "Base models are structurally calibrated and therefore forced to incur hallucination whenever IIV misclassification is non-negligible"
polarity: enables
related:
- '[[2509.04664--why-language-models-hallucinate]]'
- '[[calibration]]'
- '[[hallucination]]'
- '[[iiv-reduction]]'
- '[[singleton-rate]]'
- '[[rlhf-degrades-conditional-calibration]]'
relationships:
- type: supported_by
  target: '[[2509.04664--why-language-models-hallucinate]]'
  target_id: paper:2509.04664
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[iiv-reduction]]'
  target_id: method:iiv-reduction
  confidence: high
- type: related_to
  target: '[[singleton-rate]]'
  target_id: metric:singleton-rate
  confidence: high
- type: related_to
  target: '[[rlhf-degrades-conditional-calibration]]'
  target_id: mechanism:rlhf-degrades-conditional-calibration
  confidence: high
---

Section 3.1 shows delta equals the magnitude of the cross-entropy gradient with respect to a probability rescaling; near a cross-entropy local minimum delta is small, which forces Corollary 1's inequality to bind: error_rate >= 2 * IIV_misclassification - ratio - delta. Because calibration is a consequence of pretraining, hallucinations become structurally inevitable for well-trained base models on unlearnable facts. Empirical support: Figure 2 (reprinted from OpenAI 2023a) shows GPT-4 base is well-calibrated and its RL-finetuned version is not, consistent with the prediction that objectives deviating from cross-entropy degrade calibration.
