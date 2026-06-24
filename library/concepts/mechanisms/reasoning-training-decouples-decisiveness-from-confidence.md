---
aliases:
- reasoning fine-tuning decouples verbal decisiveness from internal confidence
- SFT decouples decisiveness from intrinsic confidence in LRMs
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reasoning-training-decouples-decisiveness-from-confidence
  type: mechanism
  status: canonical
cause: "Reasoning fine-tuning (SFT on chain-of-thought traces, knowledge distillation from a reasoning teacher) that optimizes for answer correctness rather than faithful confidence expression"
effect: "Verbal decisiveness changes substantially while token-probability-based internal confidence (RCC estimator) remains nearly unchanged, reducing cMFG* and widening the gap between surface linguistic hedging and the model's internal uncertainty signal"
polarity: decreases
related:
- '[[2606.03969--faithful-calibration-framework]]'
- '[[reasoning-finetuning-degrades-abstention]]'
- '[[cmfg-star]]'
- '[[faithful-calibration]]'
- '[[reasoning-fine-tuning]]'
- '[[supervised-finetuning]]'
- '[[generation-discrimination-gap]]'
- '[[verbalized-confidence]]'
relationships:
- type: supported_by
  target: '[[2606.03969--faithful-calibration-framework]]'
  target_id: paper:2606.03969
  confidence: high
- type: related_to
  target: '[[reasoning-finetuning-degrades-abstention]]'
  target_id: mechanism:reasoning-finetuning-degrades-abstention
  confidence: high
- type: related_to
  target: '[[cmfg-star]]'
  target_id: metric:cmfg-star
  confidence: high
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: high
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
---

After Synthetic-1 SFT, Llama-3.1-8B decisiveness fell from 0.793 to 0.634 on AIME while RCC internal confidence stayed nearly flat (0.882 to 0.881), yielding a cMFG*_R drop from 0.819 to 0.694. A distillation case (Qwen3-8B from DeepSeek-R1-671B) shows the opposite verbal shift: the student becomes more decisive than the teacher, yet both land at similar cMFG* because the student's internal confidence also rises. The pattern is consistent: reasoning training reshapes verbal behavior in ways not tracked by internal probability signals, making faithful calibration a training target that must be measured and optimized explicitly rather than assumed to improve alongside accuracy or fluency.
