---
aliases:
- epistemic alignment principle
- justified-confidence reward
tags:
- kg/term
- concept
- term
kg:
  id: term:epistemic-alignment
  type: term
  status: canonical
area: terms
related:
- '[[2511.07477--epistemic-pathology-polite-liar]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[calibration-humility-gap]]'
- '[[hallucination]]'
- '[[sycophancy]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[2511.07477--epistemic-pathology-polite-liar]]'
  target_id: paper:2511.07477
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[calibration-humility-gap]]'
  target_id: term:calibration-humility-gap
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
---

The principle that reward systems for LLMs should optimize for justified confidence over perceived fluency: outputs should be rewarded when assertoric force tracks available evidence, not when they satisfy surface-level cooperativeness or user approval. Requires changing what counts as a good response in RLHF rather than patching outputs after training.

**Why it matters here:** Names the target property that current RLHF training does not optimize for; frames the gap between safety alignment (helpful, harmless, polite) and epistemic alignment (grounded, calibrated, honest about uncertainty).

**Lineage:** Proposed by DeVilling (2511.07477) as the concluding principle of the paper; extends Frankfurt's bullshit analysis and epistemic virtue theory into an alignment objective.
