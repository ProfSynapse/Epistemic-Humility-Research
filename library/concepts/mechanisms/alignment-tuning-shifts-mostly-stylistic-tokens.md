---
aliases:
- Token distribution shift concentrated on stylistic tokens
- Alignment as surface style shift
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:alignment-tuning-shifts-mostly-stylistic-tokens
  type: mechanism
  status: canonical
cause: "Comparing the next-token distribution of a base LLM against its SFT- or RLHF-aligned counterpart, token by token, over held-out generations"
effect: "The vast majority of token positions are unshifted (base and aligned model agree on the top-ranked token); the small fraction that do shift concentrate on stylistic tokens (discourse markers, greetings, transition words) and safety/refusal tokens, not knowledge-bearing content tokens"
polarity: mediates
related:
- '[[2312.01552--unlocking-spell-base-llms-rethinking-alignment-context]]'
- '[[urial]]'
- '[[superficial-alignment-hypothesis]]'
- '[[instruction-tuning]]'
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
  target: '[[superficial-alignment-hypothesis]]'
  target_id: term:superficial-alignment-hypothesis
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: high
---

Lin et al. (2023) compare Llama-2-7B against Llama-2-7B-Chat token-by-token across 1,000 examples: 77.7% of token positions are exactly unshifted (same top-ranked token), rising to 92.2% when including "marginal" near-ties (Section 2.2, Figure 3). Across three base-vs-aligned pairs at the 7B scale (Llama-2 base vs. Llama-2-Chat/RLHF, Llama-2 base vs. Vicuna-7B/SFT, Mistral base vs. Mistral-Instruct/SFT), the shifted-token ratio is consistently only 5-7%, and the shifted tokens overlap heavily across pairs: discourse markers and openers ("Thank", "Hello", "Of course", "Please"), list-structuring tokens ("Here", "including", "1."), and safety/refusal tokens ("However", "sorry", "must point out", "apolog[ize]"). Knowledge-bearing content (the actual answer and supporting facts) appears at unshifted positions in both base and aligned models. This is the direct token-level evidence behind the [[superficial-alignment-hypothesis]]: alignment tuning mostly relocates probability mass onto a small set of stylistic and safety tokens rather than teaching new content.
