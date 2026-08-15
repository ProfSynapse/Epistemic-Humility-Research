---
aliases:
- Base plus 3 ICL examples matches SFT/RLHF
- URIAL closes the alignment gap without tuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:icl-only-alignment-matches-sft-rlhf-quality
  type: mechanism
  status: canonical
cause: "Prompting a strong base LLM with [[urial]] (a fixed system prompt plus K=3 constant restyled in-context demonstrations, zero gradient updates)"
effect: "Response quality on just-eval-instruct matches, and on well-pretrained base models exceeds, the quality of the same model's official SFT- or RLHF-tuned counterpart"
polarity: enables
related:
- '[[2312.01552--unlocking-spell-base-llms-rethinking-alignment-context]]'
- '[[urial]]'
- '[[in-context-learning]]'
- '[[small-scale-curated-sft-approaches-rlhf-preference-parity]]'
relationships:
- type: supported_by
  target: '[[2312.01552--unlocking-spell-base-llms-rethinking-alignment-context]]'
  target_id: paper:2312.01552
  confidence: high
- type: related_to
  target: '[[urial]]'
  target_id: method:urial
  confidence: high
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: high
- type: related_to
  target: '[[small-scale-curated-sft-approaches-rlhf-preference-parity]]'
  target_id: mechanism:small-scale-curated-sft-approaches-rlhf-preference-parity
  confidence: medium
---

On Llama-2-7B, URIAL (tuning-free) reaches an overall just-eval-instruct score of 4.33, comparable to that base model's own SFT/RLHF-tuned versions, clearly ahead of zero-shot templated prompting (3.05-3.14) and vanilla K=3 in-context learning (3.18). On stronger base models the gap flips: URIAL on Mistral-7B scores 4.63 versus 4.44 for the official Mistral-7B-Instruct (SFT); URIAL on Llama-2-70B scores 4.74 versus 4.67 for Llama-2-70B-Chat (RLHF), approaching ChatGPT (4.75) and GPT-4 (4.8) (Section 4.3, Table 1; corroborated by a human pairwise study, Table 2). Lin et al. (2023) conclude that when the base LLM is well-pretrained, SFT and RLHF may not be as crucial for alignment quality as previously believed, since tuning-free in-context alignment can match or exceed them.
