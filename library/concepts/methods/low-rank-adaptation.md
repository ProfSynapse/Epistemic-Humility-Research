---
aliases:
- LoRA
- LoRA tuning
- parameter-efficient fine-tuning
- PEFT
- low-rank-adaptation
tags:
- kg/method
- concept
- method
kg:
  id: method:low-rank-adaptation
  type: method
  status: canonical
area: methods
related:
- '[[2311.13240--calibration-of-llms-and-alignment]]'
- '[[supervised-finetuning]]'
- '[[instruction-tuning]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[lora-regularizes-calibration]]'
relationships:
- type: proposed_by
  target: '[[2311.13240--calibration-of-llms-and-alignment]]'
  target_id: paper:2311.13240
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[lora-regularizes-calibration]]'
  target_id: mechanism:lora-regularizes-calibration
  confidence: medium
---

A parameter-efficient fine-tuning method that keeps pretrained weights frozen and injects trainable low-rank decomposition matrices into each Transformer layer, reducing the number of updated parameters by orders of magnitude (Hu et al., 2021).

**Why it matters here:** Empirically acts as a calibration regularizer during instruction tuning: Zhu et al. find LoRA-tuned models consistently outperform fully fine-tuned models in ECE across all tasks and datasets, with deterioration typically in the range of 0.001 per calibration measurement as training epochs increase. Originally motivated for compute efficiency but has this secondary calibration benefit.

**Lineage:** Introduced by Hu et al. (2021). Used in Alpaca-LoRA, instruction-tuned LLaMA variants, and many downstream RLHF pipelines. Adopted by Zhu et al. (2311.13240) in both the SFT and RLHF stages.
