---
aliases:
- VA subspace
- valence arousal geometry
- VA plane
- circumplex emotion geometry in LLMs
tags:
- kg/term
- concept
- term
kg:
  id: term:valence-arousal-subspace
  type: term
  status: canonical
area: terms
related:
- '[[2604.03147--sycophancy-internal-representations]]'
- '[[va-subspace-extraction]]'
- '[[goemotions]]'
- '[[steering-vector]]'
- '[[refusal-direction]]'
- '[[sycophancy]]'
- '[[truth-direction]]'
- '[[activation-addition]]'
relationships:
- type: proposed_by
  target: '[[2604.03147--sycophancy-internal-representations]]'
  target_id: paper:2604.03147
  confidence: high
- type: related_to
  target: '[[va-subspace-extraction]]'
  target_id: method:va-subspace-extraction
  confidence: medium
- type: related_to
  target: '[[goemotions]]'
  target_id: dataset:goemotions
  confidence: medium
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: medium
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: medium
- type: related_to
  target: '[[activation-addition]]'
  target_id: method:activation-addition
  confidence: medium
---

A two-dimensional linear subspace in LLM activation space spanned by a recovered valence axis (pleasure-displeasure) and arousal axis (activation-deactivation), learned via PCA decomposition of emotion steering vectors followed by ridge regression. Emotion steering vectors projected onto this subspace arrange in a circle, mirroring Russell's circumplex model of human core affect.

**Why it matters here:** Provides a continuous, interpretable substrate for multi-behavioral control: steering along valence and arousal axes shifts both affective properties of generated text and downstream behaviors (refusal, sycophancy) more effectively than discrete emotion or task-specific contrastive directions.

**Lineage:** Theoretical basis from Russell 1980 (circumplex model of affect); operationalized in LLMs by 2604.03147.
