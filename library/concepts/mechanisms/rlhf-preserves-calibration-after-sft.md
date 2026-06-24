---
aliases:
- RLHF does not compound SFT calibration harm
- PPO no additional calibration degradation after instruction tuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-preserves-calibration-after-sft
  type: mechanism
  status: canonical
cause: "Applying RLHF (PPO) to a language model that has already undergone instruction tuning ([[supervised-finetuning]] on Alpaca)"
effect: "No significant additional ECE degradation beyond the SFT baseline, across CLM, factual entity prediction, and MMLU, even after 3 RLHF epochs"
polarity: mediates
related:
- '[[2311.13240--calibration-of-llms-and-alignment]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[rlhf-degrades-conditional-calibration]]'
- '[[instruction-tuning-degrades-logit-calibration]]'
relationships:
- type: supported_by
  target: '[[2311.13240--calibration-of-llms-and-alignment]]'
  target_id: paper:2311.13240
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
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
  target: '[[rlhf-degrades-conditional-calibration]]'
  target_id: mechanism:rlhf-degrades-conditional-calibration
  confidence: high
- type: related_to
  target: '[[instruction-tuning-degrades-logit-calibration]]'
  target_id: mechanism:instruction-tuning-degrades-logit-calibration
  confidence: high
---

When RLHF is applied on top of an already instruction-tuned model (Alpaca-SFT LLaMA-7B), the calibration cost of the SFT stage has already been paid and PPO does not compound it. Zhu et al. (2311.13240) find no significant further ECE increase after 3 RLHF epochs in any of the three tasks (Figure 5, last bar groups; Table 3). This is qualified: it applies to PPO starting from an SFT checkpoint, using GPT-4-ranked response data. It partially contrasts with the rlhf-degrades-conditional-calibration mechanism documented in 2305.14975 (just-ask-for-calibration), where the starting point and training conditions differ. The reconciliation is that SFT absorbs most of the calibration cost, leaving RLHF with little remaining degradation to introduce.
