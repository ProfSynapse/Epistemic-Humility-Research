---
aliases:
- NRC VAD
- NRC-VAD v2
- Mohammad NRC-VAD
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:nrc-vad-lexicon
  type: dataset
  status: canonical
area: datasets
related:
- '[[2604.03147--sycophancy-internal-representations]]'
- '[[va-subspace-extraction]]'
- '[[valence-arousal-subspace]]'
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
  target: '[[valence-arousal-subspace]]'
  target_id: term:valence-arousal-subspace
  confidence: medium
---

A human-crowdsourced lexical resource providing valence, arousal, and dominance scores for 44,728 English words on a 0-1 scale, collected by Mohammad (2025). Used to validate that learned VA subspace projections align with human affect ratings.

**Why it matters here:** Serves as the held-out gold standard for validating that a learned VA subspace encodes semantically meaningful affect dimensions rather than arbitrary directions; alignment at r=0.71 for valence confirms the subspace captures human-interpretable content.

**Lineage:** Mohammad 2025 (NRC, Canada); used in 2604.03147 Section 4.1 for lexical validation.
