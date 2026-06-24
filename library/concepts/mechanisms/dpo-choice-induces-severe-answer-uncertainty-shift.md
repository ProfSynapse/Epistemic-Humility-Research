---
aliases:
- DPO answer-contrastive pairs cause worst-case overconfidence
- DPO-Choice overconfidence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-choice-induces-severe-answer-uncertainty-shift
  type: mechanism
  status: canonical
cause: "Direct preference optimization using pairs that share the same format but differ in which choice is labeled preferred (DPO-Choice scheme)"
effect: "The model's answer uncertainty shifts most severely toward overconfidence on held-out MCQ tasks among all alignment conditions tested"
polarity: increases
related:
- '[[2310.11732--calibration-aligned-multiple-choice]]'
- '[[answer-uncertainty]]'
- '[[format-uncertainty]]'
- '[[direct-preference-optimization]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[alignment-conflates-answer-and-format-uncertainty]]'
- '[[dpo-eliminates-reward-model]]'
relationships:
- type: supported_by
  target: '[[2310.11732--calibration-aligned-multiple-choice]]'
  target_id: paper:2310.11732
  confidence: high
- type: related_to
  target: '[[answer-uncertainty]]'
  target_id: term:answer-uncertainty
  confidence: high
- type: related_to
  target: '[[format-uncertainty]]'
  target_id: term:format-uncertainty
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[alignment-conflates-answer-and-format-uncertainty]]'
  target_id: mechanism:alignment-conflates-answer-and-format-uncertainty
  confidence: high
- type: related_to
  target: '[[dpo-eliminates-reward-model]]'
  target_id: mechanism:dpo-eliminates-reward-model
  confidence: high
---

When DPO preference pairs contrast only on the choice letter (same format, different answer), the optimization maximally updates the token probabilities over choice letters in the direction of the preferred answer. Because this update is applied across the full vocabulary and propagates through the model, it generalizes as answer-uncertainty inflation to tasks not covered during training. He et al. 2023 show that DPO-Choice produces the most severe overconfident tendency on MMLU among all six synthetic alignment conditions (Figure 7, §4.3), more severe than SFT-Choice or DPO-Mixed. In the Mistral-to-Zephyr pipeline, the DPO step (which is preference-based and answer-contrastive) sharply increases confidence relative to the SFT-only checkpoint, while the SFT step leaves confidence unchanged (Figure 5, §4.2).
