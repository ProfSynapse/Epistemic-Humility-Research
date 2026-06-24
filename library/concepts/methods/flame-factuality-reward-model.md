---
aliases:
- RM^fact
- factuality reward model
- atomic-fact retrieval reward
tags:
- kg/method
- concept
- method
kg:
  id: method:flame-factuality-reward-model
  type: method
  status: canonical
area: methods
related:
- '[[2405.01525--flame-factuality-aware-alignment]]'
- '[[factscore]]'
- '[[reward-model]]'
- '[[flame-factuality-aware-alignment]]'
- '[[direct-preference-optimization]]'
relationships:
- type: proposed_by
  target: '[[2405.01525--flame-factuality-aware-alignment]]'
  target_id: paper:2405.01525
  confidence: high
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
- type: related_to
  target: '[[flame-factuality-aware-alignment]]'
  target_id: method:flame-factuality-aware-alignment
  confidence: medium
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
---

A retrieval-augmented factuality scorer used in DPO^flame that decomposes a response into atomic facts, retrieves supporting passages for each, and verifies each claim, outputting the percentage of facts that are correct. Best configuration uses Instruct Llama-2 7B with 10 retrieved passages (Kendall tau 0.34 with FAVA human hallucination annotations).

**Why it matters here:** Provides a factuality-specific reward signal that can be combined with instruction-following preference data during DPO, decoupling factual accuracy from helpfulness optimization.

**Lineage:** Draws on FActScore methodology (Min et al. 2023) for atomic-fact decomposition and retrieval-augmented verification; applied as an offline reward model rather than an evaluation metric.
