---
aliases:
- LoRA adapter ensemble
- LoRA ensemble uncertainty
- multi-adapter ensemble
tags:
- kg/method
- concept
- method
kg:
  id: method:lora-ensemble
  type: method
  status: canonical
area: methods
related:
- '[[2603.24967--uncertainty-source-decomposition]]'
- '[[uncertainty-source-decomposition]]'
- '[[knowledge-gap]]'
- '[[supervised-finetuning]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2603.24967--uncertainty-source-decomposition]]'
  target_id: paper:2603.24967
  confidence: high
- type: related_to
  target: '[[uncertainty-source-decomposition]]'
  target_id: method:uncertainty-source-decomposition
  confidence: medium
- type: related_to
  target: '[[knowledge-gap]]'
  target_id: term:knowledge-gap
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

An ensemble uncertainty estimation method that trains M independent LoRA adapters (low-rank adaptation modules) on the same dataset with different random seeds, then measures disagreement across the M adapter outputs as a proxy for knowledge-gap uncertainty. In the reference implementation: M=5, rank r=8, alpha=32, dropout 0.1, learning rate 2e-5, batch size 4, 1 epoch, max sequence length 1024.

**Why it matters here:** Provides a tractable compute budget for knowledge-gap uncertainty estimation that leverages existing LoRA fine-tuning infrastructure. Compatible with the locked training-regimen experimental setup, which already trains LoRA adapters across SFT/DPO/KTO arms.

**Lineage:** Instantiated in Taparia et al. 2026 (arXiv:2603.24967) as the knowledge-gap estimation arm of the uncertainty-source-decomposition framework.
