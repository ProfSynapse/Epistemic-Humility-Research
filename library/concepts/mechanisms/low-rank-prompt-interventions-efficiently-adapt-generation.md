---
aliases:
- Low-rank prompt interventions adapt generation with few parameters
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:low-rank-prompt-interventions-efficiently-adapt-generation
  type: mechanism
  status: canonical
cause: "[[low-rank-linear-subspace-reft]] edits selected prompt-token hidden representations in learned low-rank subspaces."
effect: "A frozen language model is adapted to downstream generation tasks with fewer trainable parameters than the compared weight-based methods."
polarity: enables
related:
- '[[2404.03592--reft-representation-finetuning-language-models]]'
- '[[low-rank-linear-subspace-reft]]'
- '[[representation-finetuning]]'
- '[[low-rank-adaptation]]'
relationships:
- type: supported_by
  target: '[[2404.03592--reft-representation-finetuning-language-models]]'
  target_id: paper:2404.03592
  confidence: high
- type: related_to
  target: '[[low-rank-linear-subspace-reft]]'
  target_id: method:low-rank-linear-subspace-reft
  confidence: high
- type: related_to
  target: '[[representation-finetuning]]'
  target_id: method:representation-finetuning
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

Across commonsense reasoning and instruction following, the paper reports that
LoReFT exceeded the compared PEFT methods while training 15 to 65 times fewer
parameters than LoRA. The arithmetic results qualify this pattern because
LoReFT did not outperform LoRA or adapters there.
