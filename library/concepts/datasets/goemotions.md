---
aliases:
- GoEmotions dataset
- Go Emotions
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:goemotions
  type: dataset
  status: canonical
area: datasets
related:
- '[[2604.03147--sycophancy-internal-representations]]'
- '[[sycophancy]]'
- '[[steering-vector]]'
- '[[va-subspace-extraction]]'
relationships:
- type: proposed_by
  target: '[[2604.03147--sycophancy-internal-representations]]'
  target_id: paper:2604.03147
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: medium
- type: related_to
  target: '[[va-subspace-extraction]]'
  target_id: method:va-subspace-extraction
  confidence: medium
---

A large-scale, fine-grained emotion dataset of 211,225 English Reddit comments annotated with 27 emotion labels plus a neutral class, released by Demszky et al. (2020). Provides single-label and multi-label subsets; the single-label subset is the standard source for emotion steering vector extraction.

**Why it matters here:** Primary training corpus for deriving emotion steering vectors in the VA subspace extraction pipeline; its 27 discrete emotion categories span the full circumplex and enable full-circle reconstruction of the VA geometry.

**Lineage:** Demszky et al. 2020 (Google); used in 2604.03147 for emotion steering vector extraction.
