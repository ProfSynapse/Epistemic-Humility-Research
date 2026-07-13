---
aliases:
- frequency-based summarization
- sample-then-summarize SFT
- consensus summarization
- LC SFT bootstrapping
tags:
- kg/method
- concept
- method
kg:
  id: method:summary-distillation
  type: method
  status: canonical
area: methods
related:
- '[[2404.00474--linguistic-calibration-long-form]]'
- '[[linguistic-calibration-lc]]'
- '[[supervised-finetuning]]'
- '[[verbalized-confidence]]'
- '[[self-consistency]]'
relationships:
- type: proposed_by
  target: '[[2404.00474--linguistic-calibration-long-form]]'
  target_id: paper:2404.00474
  confidence: high
- type: related_to
  target: '[[linguistic-calibration-lc]]'
  target_id: method:linguistic-calibration-lc
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
---

A supervised fine-tuning bootstrapping technique that samples M long-form responses from a base LM for each query, prompts an API-based LLM to summarize them into a consensus paragraph with claim-level confidence statements calibrated to sample frequency (e.g., 'I estimate a 30% chance...'), and then fine-tunes the base model on (query, summary) pairs. Generalizes Self-Consistency from short-answer confidence elicitation to long-form multi-claim generations.

**Why it matters here:** Produces an LC SFT initial policy capable of expressing graded verbal confidence without any human annotation, using only a base model and an API-based LLM for the summarization step. The recipe is reusable for any base model with white-box access, including the Qwen3 checkpoints in the locked training-regimen study, to create a calibration-first SFT variant for comparison against DPO/KTO abstention arms.

**Lineage:** proposed by Band et al. (2024) in the LC framework; inspired by self-consistency; related to supervised-finetuning and verbalized-confidence
