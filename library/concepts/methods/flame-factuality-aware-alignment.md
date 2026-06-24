---
aliases:
- FLAME
- SFT^flame
- DPO^flame
- factuality-aware SFT
- factuality-aware DPO
tags:
- kg/method
- concept
- method
kg:
  id: method:flame-factuality-aware-alignment
  type: method
  status: canonical
area: methods
related:
- '[[2405.01525--flame-factuality-aware-alignment]]'
- '[[direct-preference-optimization]]'
- '[[supervised-finetuning]]'
- '[[reward-model]]'
- '[[factscore]]'
- '[[hallucination]]'
- '[[sft-unknown-examples-drive-hallucination]]'
- '[[rlhf-helpfulness-bias-suppresses-refusal]]'
relationships:
- type: proposed_by
  target: '[[2405.01525--flame-factuality-aware-alignment]]'
  target_id: paper:2405.01525
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[sft-unknown-examples-drive-hallucination]]'
  target_id: mechanism:sft-unknown-examples-drive-hallucination
  confidence: medium
- type: related_to
  target: '[[rlhf-helpfulness-bias-suppresses-refusal]]'
  target_id: mechanism:rlhf-helpfulness-bias-suppresses-refusal
  confidence: medium
---

A two-stage alignment method that (1) in the SFT stage classifies instructions as fact-requiring or not and replaces human-authored targets with the pre-trained model's own few-shot generations for fact-requiring instructions, and (2) in the DPO stage augments instruction-following preference pairs with a separate factuality preference track built from a retrieval-augmented atomic-fact reward model, applied only to fact-requiring instructions.

**Why it matters here:** Shows that factuality and instruction following can be jointly improved without a tradeoff by routing supervision to the appropriate source for each instruction type, and by decoupling the factuality reward from the helpfulness reward during DPO.

**Lineage:** Extends self-rewarding language models (Yuan et al. 2024) by adding a factuality reward track and instruction-type routing; the DPO factuality preference construction is related to Tian et al. 2024 but FLAME additionally preserves instruction-following capability.
