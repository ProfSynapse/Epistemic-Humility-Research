---
aliases:
- LoRA mitigates calibration degeneration
- parameter-efficient tuning regularizes ECE
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:lora-regularizes-calibration
  type: mechanism
  status: canonical
cause: "Using [[low-rank-adaptation]] (LoRA) instead of full parameter fine-tuning during instruction tuning"
effect: "ECE deterioration across training epochs is substantially smaller than under full fine-tuning; models retain better-calibrated output probabilities across CLM, factual, and reasoning tasks"
polarity: decreases
related:
- '[[2311.13240--calibration-of-llms-and-alignment]]'
- '[[low-rank-adaptation]]'
- '[[instruction-tuning]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[instruction-tuning-degrades-logit-calibration]]'
- '[[supervised-finetuning]]'
relationships:
- type: supported_by
  target: '[[2311.13240--calibration-of-llms-and-alignment]]'
  target_id: paper:2311.13240
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
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
  target: '[[instruction-tuning-degrades-logit-calibration]]'
  target_id: mechanism:instruction-tuning-degrades-logit-calibration
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
---

LoRA keeps pretrained weights frozen and only updates a small set of injected low-rank matrices, limiting the distributional shift applied to the base model's probability estimates. This acts as implicit regularization against calibration erosion. Zhu et al. (2311.13240) find that LoRA-trained models consistently outperform fully fine-tuned models in ECE across all instruction datasets (Alpaca and OA) and all three evaluation tasks, with ECE deterioration described as 'often in a level of 0.001' per calibration measurement while full fine-tuning produces visibly worse ECE. Originally designed for compute efficiency, the calibration benefit is a secondary finding.
