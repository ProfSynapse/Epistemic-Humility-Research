---
aliases:
- CSS
- specificity score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:certificate-specificity-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2606.08571--structured-ignorance-certificates]]'
- '[[structured-ignorance-certificates]]'
- '[[unknown-unknown-dataset]]'
- '[[knowledge-boundary]]'
- '[[abstention-rate]]'
relationships:
- type: proposed_by
  target: '[[2606.08571--structured-ignorance-certificates]]'
  target_id: paper:2606.08571
  confidence: high
- type: related_to
  target: '[[structured-ignorance-certificates]]'
  target_id: method:structured-ignorance-certificates
  confidence: medium
- type: related_to
  target: '[[unknown-unknown-dataset]]'
  target_id: dataset:unknown-unknown-dataset
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
---

A scalar metric measuring how precisely a Structured Ignorance Certificate identifies the missing concepts and domain intersection required to answer an unknown-unknown query. A mean score of 0.967 is reported on 735 held-out UU questions.

**Why it matters here:** Operationalizes the quality of structured ignorance declarations beyond format validity, capturing whether the model correctly diagnoses what knowledge it lacks rather than producing a generic placeholder.

**Lineage:** Introduced in Sahoo 2026 (arXiv 2606.08571) as the primary quality metric for SIC outputs.
