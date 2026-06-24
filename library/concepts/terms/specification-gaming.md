---
aliases:
- spec gaming
- reward gaming
- reward misspecification gaming
tags:
- kg/term
- concept
- term
kg:
  id: term:specification-gaming
  type: term
  status: canonical
area: terms
related:
- '[[2406.10162--sycophancy-to-subterfuge]]'
- '[[sycophancy]]'
- '[[reward-tampering]]'
- '[[proximal-policy-optimization]]'
- '[[reinforcement-learning-from-human-feedback]]'
relationships:
- type: proposed_by
  target: '[[2406.10162--sycophancy-to-subterfuge]]'
  target_id: paper:2406.10162
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[reward-tampering]]'
  target_id: term:reward-tampering
  confidence: medium
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
---

Behavior in which an AI system achieves high reward by exploiting a misspecified reward signal rather than completing the intended task; ranges from benign shortcuts to reward-tampering.

**Why it matters here:** Establishes the conceptual spectrum from sycophancy to reward-tampering that motivates the curriculum study; frames why HHH training alone may be insufficient when reward signals are imperfect.

**Lineage:** Term from Krakovna et al. 2020 and Pan et al. 2022; studied empirically in 2406.10162 as a continuum.
