---
aliases:
- maximum confidence metric
- largest-bin fraction
- max-conf factuality metric
tags:
- kg/method
- concept
- method
kg:
  id: method:max-confidence-scoring
  type: method
  status: canonical
area: methods
related:
- '[[2311.08401--finetuning-for-factuality]]'
- '[[consistency-based-confidence]]'
- '[[facttune-mc]]'
- '[[factscore]]'
- '[[self-consistency]]'
- '[[facttune-fs]]'
relationships:
- type: proposed_by
  target: '[[2311.08401--finetuning-for-factuality]]'
  target_id: paper:2311.08401
  confidence: high
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[facttune-mc]]'
  target_id: method:facttune-mc
  confidence: medium
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[facttune-fs]]'
  target_id: method:facttune-fs
  confidence: medium
---

A reference-free factuality scoring method that resamples a model's answer to a given question multiple times, bins answers by semantic equivalence (typically via heuristic string matching), and reports the fraction of answers falling into the largest bin as the confidence score for that fact. A higher score signals that the model is more consistently committed to one answer, serving as a proxy for factual reliability.

**Why it matters here:** Outperforms entropy over semantic bins in the atomic-question setting on biographies (0.840 vs 0.810 % Correct) and is the preferred scoring design choice in FactTune-MC. The mechanism connects directly to Phase 1's use of consistency-based signals as epistemic surrogates and to mechanism program probing of self-consistency representations.

**Lineage:** Variant of consistency-based-confidence; compared against semantic entropy in the same experimental setup; used as the scoring core of facttune-mc.
