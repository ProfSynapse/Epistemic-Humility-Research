---
aliases:
- valence-arousal subspace learning
- PCA ridge regression emotion decomposition
- VA axis recovery
tags:
- kg/method
- concept
- method
kg:
  id: method:va-subspace-extraction
  type: method
  status: canonical
area: methods
related:
- '[[2604.03147--sycophancy-internal-representations]]'
- '[[goemotions]]'
- '[[nrc-vad-lexicon]]'
- '[[valence-arousal-subspace]]'
- '[[steering-vector]]'
- '[[contrastive-activation-addition]]'
- '[[representation-engineering]]'
relationships:
- type: proposed_by
  target: '[[2604.03147--sycophancy-internal-representations]]'
  target_id: paper:2604.03147
  confidence: high
- type: related_to
  target: '[[goemotions]]'
  target_id: dataset:goemotions
  confidence: medium
- type: related_to
  target: '[[nrc-vad-lexicon]]'
  target_id: dataset:nrc-vad-lexicon
  confidence: medium
- type: related_to
  target: '[[valence-arousal-subspace]]'
  target_id: term:valence-arousal-subspace
  confidence: medium
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: medium
- type: related_to
  target: '[[contrastive-activation-addition]]'
  target_id: method:contrastive-activation-addition
  confidence: medium
- type: related_to
  target: '[[representation-engineering]]'
  target_id: method:representation-engineering
  confidence: medium
---

A three-stage pipeline for identifying valence and arousal axes in LLM representations: (1) compute emotion steering vectors as mean-difference contrasts between emotion-labeled and neutral hidden states using GoEmotions; (2) elicit the model's self-reported VA coordinates for each emotion category; (3) fit VA axes as linear combinations of the top principal components of the emotion vectors via ridge regression to recover the self-reported scores. The resulting axes exhibit circular geometry in the learned subspace.

**Why it matters here:** Provides a reusable, domain-agnostic control basis that generalizes across multiple downstream behaviors (refusal, sycophancy) from a single subspace, outperforming single-task contrastive directions on sycophancy reduction by up to 21 percentage points.

**Lineage:** Proposed in 2604.03147 (Sun et al. 2026, Shanghai AI Lab / University of Chicago).
