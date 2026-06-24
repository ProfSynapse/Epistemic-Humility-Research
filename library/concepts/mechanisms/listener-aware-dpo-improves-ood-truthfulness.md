---
aliases:
- LACIE OOD transfer
- pragmatic calibration generalizes cross-domain
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:listener-aware-dpo-improves-ood-truthfulness
  type: mechanism
  status: canonical
cause: "LACIE DPO finetuning on TriviaQA with listener-acceptance signal"
effect: "TruthfulQA truthfulness rises from 0.27 to 0.55 (+28 points absolute) at a 9-point informativeness cost, exceeding the truthful-only DPO baseline of 0.39"
polarity: enables
related:
- '[[2405.21028--lacie-listener-aware-calibration]]'
- '[[lacie]]'
- '[[truthfulqa]]'
- '[[triviaqa]]'
- '[[calibration]]'
- '[[calibration-hallucination-tradeoff]]'
- '[[pretrained-latent-representations-enable-calibration-generalization]]'
- '[[listener-aware-preference-induces-emergent-abstention]]'
relationships:
- type: supported_by
  target: '[[2405.21028--lacie-listener-aware-calibration]]'
  target_id: paper:2405.21028
  confidence: high
- type: related_to
  target: '[[lacie]]'
  target_id: method:lacie
  confidence: high
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[calibration-hallucination-tradeoff]]'
  target_id: mechanism:calibration-hallucination-tradeoff
  confidence: high
- type: related_to
  target: '[[pretrained-latent-representations-enable-calibration-generalization]]'
  target_id: mechanism:pretrained-latent-representations-enable-calibration-generalization
  confidence: high
- type: related_to
  target: '[[listener-aware-preference-induces-emergent-abstention]]'
  target_id: mechanism:listener-aware-preference-induces-emergent-abstention
  confidence: high
---

A LACIE-trained Mistral-7B that saw only TriviaQA preferences during training reaches 0.55 truthfulness on the 817-question TruthfulQA evaluation split versus 0.27 base and 0.39 truthful-only DPO (Table 3). The gain reflects the model's learned tendency to hedge when uncertain rather than generating plausible-sounding but false content. The 9-point informativeness drop (0.99 to 0.90) is driven primarily by increased abstention on uncertain questions, consistent with the tradeoff documented in calibration-hallucination-tradeoff. The cross-domain transfer suggests the listener-grounded preference signal instills a general calibration posture rather than dataset-specific surface cues. (Table 3, Section 5)
