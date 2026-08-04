---
aliases:
- QLoRA
- Quantized Low-Rank Adaptation
tags:
- kg/method
- concept
- method
kg:
  id: method:qlora
  type: method
  status: canonical
area: methods
related:
- '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
- '[[layer-pruning]]'
relationships:
- type: used_by
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
- type: related_to
  target: '[[layer-pruning]]'
  target_id: method:layer-pruning
  confidence: medium
---

QLoRA is a parameter-efficient finetuning (PEFT) method that combines 4-bit
quantization of a frozen pretrained model's weights with trainable low-rank
adapter (LoRA) matrices injected into the linear layers, so that finetuning a
large model requires only a fraction of the memory of full finetuning or
16-bit LoRA.

**Why it matters here:** Used as the "healing" step after layer pruning:
because each pruning experiment is run on a single 40GB A100 GPU, QLoRA's
memory footprint is what makes it feasible to finetune away the distribution
shift introduced by removing a block of layers, across model sizes up to
70B parameters.

**Lineage:** originally introduced by Dettmers et al. (no paper atom yet in
this vault); applied as the healing method for [[layer-pruning]] in
arXiv:2403.17887.
