---
aliases:
- frequency threshold
- linearity threshold
- co-occurrence threshold
- Pretraining Co-occurrence Threshold for Linear Representations
tags:
- kg/term
- concept
- term
kg:
  id: term:pretraining-co-occurrence-threshold
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
- '[[subject-object-co-occurrence-frequency]]'
- '[[linear-relation-embedding]]'
- '[[lre-causality]]'
relationships:
- type: proposed_by
  target: '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
  target_id: paper:2504.12459
  confidence: high
- type: related_to
  target: '[[subject-object-co-occurrence-frequency]]'
  target_id: term:subject-object-co-occurrence-frequency
- type: related_to
  target: '[[linear-relation-embedding]]'
  target_id: method:linear-relation-embedding
---

The pretraining co-occurrence threshold is the empirically identified subject-object co-occurrence count above which LRE causality consistently exceeds 0.9 (near-perfect linearity): approximately 1k co-occurrences for OLMo-7B and 2k for GPT-J. Below this threshold, the factual relation is not reliably encoded as a linear transformation of the subject representation, so recall is unstable. The threshold holds regardless of when in the pretraining trajectory those co-occurrences accumulate, suggesting it is a count-based rather than timing-based phenomenon.

**Why it matters here:** The threshold defines a sharp empirical boundary between facts a model has internalized linearly and those it has not, providing a mechanistic correlate for the known-unknowns divide that epistemic humility must navigate.

**Lineage:** defined in [[2504.12459--linear-representations-pretraining-data-frequency-language-models]]; operationalizes [[subject-object-co-occurrence-frequency]] as a threshold over [[lre-causality]].
