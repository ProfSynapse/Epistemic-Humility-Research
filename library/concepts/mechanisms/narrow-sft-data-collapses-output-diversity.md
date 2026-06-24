---
aliases:
- SFT data breadth determines diversity floor
- two-teacher distillation collapses diversity
- SFT homogeneity from narrow teacher set
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:narrow-sft-data-collapses-output-diversity
  type: mechanism
  status: canonical
cause: "Supervised fine-tuning on completions from a small number of teachers (two in Think: QwQ-32B and DeepSeek-R1) produces a low-entropy target distribution in the same restricted region of output space"
effect: "The model loses 62% of Base SBERT semantic diversity on average across 15 tasks, with steeper collapse on easier tasks (GSM8K 36% retained) and shallower collapse on harder tasks (MATH-Geometry 54% retained); multi-source SFT data mitigates the collapse"
polarity: decreases
related:
- '[[2604.16027--posttraining-diversity-collapse]]'
- '[[output-diversity-collapse]]'
- '[[supervised-finetuning]]'
- '[[reasoning-fine-tuning]]'
- '[[dpo-diversity-cost-depends-on-upstream-sft-state]]'
relationships:
- type: supported_by
  target: '[[2604.16027--posttraining-diversity-collapse]]'
  target_id: paper:2604.16027
  confidence: high
- type: related_to
  target: '[[output-diversity-collapse]]'
  target_id: term:output-diversity-collapse
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[reasoning-fine-tuning]]'
  target_id: method:reasoning-fine-tuning
  confidence: high
- type: related_to
  target: '[[dpo-diversity-cost-depends-on-upstream-sft-state]]'
  target_id: mechanism:dpo-diversity-cost-depends-on-upstream-sft-state
  confidence: high
---

Cross-entropy training on narrow two-teacher distillation data performs maximum-likelihood estimation on a low-entropy target. The two teachers produce completions occupying a restricted region of output space, and the model reproduces this narrow mixture. Instruct-SFT, despite initializing from the already-collapsed Think-SFT, recovers a median 40% of the lost diversity by training on broader multi-source data. Collapse magnitude scales with task difficulty: tasks with a dominant solution strategy (GSM8K 92% accuracy) collapse more than tasks where strategies vary (MATH-Geometry 50% accuracy). This mechanism is not reversed by switching generation format at inference.
