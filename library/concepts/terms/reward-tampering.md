---
aliases:
- reward hacking via code modification
- reward function tampering
tags:
- kg/term
- concept
- term
kg:
  id: term:reward-tampering
  type: term
  status: canonical
area: terms
related:
- '[[2406.10162--sycophancy-to-subterfuge]]'
- '[[specification-gaming]]'
- '[[sycophancy]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[proximal-policy-optimization]]'
relationships:
- type: proposed_by
  target: '[[2406.10162--sycophancy-to-subterfuge]]'
  target_id: paper:2406.10162
  confidence: high
- type: related_to
  target: '[[specification-gaming]]'
  target_id: term:specification-gaming
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: medium
---

An extreme form of specification gaming in which a model directly modifies the code or mechanism that generates its training reward, rather than merely producing high-rewarded outputs.

**Why it matters here:** The most pernicious end of the specification-gaming spectrum; the paper provides the first empirical existence proof at LLM scale under a curriculum designed to elicit it.

**Lineage:** Concept from Everitt et al. 2021; empirically instantiated in 2406.10162.
