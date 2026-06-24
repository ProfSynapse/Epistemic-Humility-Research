---
aliases:
- UU dataset
- cross-domain UU dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:unknown-unknown-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[2606.08571--structured-ignorance-certificates]]'
- '[[structured-ignorance-certificates]]'
- '[[knowledge-boundary]]'
- '[[known-unknowns-taxonomy]]'
- '[[abstention-generalization-failure]]'
- '[[hallucination]]'
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
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: medium
- type: related_to
  target: '[[abstention-generalization-failure]]'
  target_id: mechanism:abstention-generalization-failure
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
---

A 7,347-sample training set constructed by prompting Qwen3-14B to stitch questions from seven domains (physics, biology, engineering, CS, economics, medical, legal) into novel cross-domain queries that no single-domain expert could answer, with 735 held-out evaluation questions. Designed to elicit the unknown-unknown failure mode in reasoning models.

**Why it matters here:** Provides a controlled training and evaluation resource specifically targeting knowledge-boundary failures that arise from domain intersection, rather than simple factual recall gaps.

**Lineage:** Constructed in Sahoo 2026 (arXiv 2606.08571). No prior dataset targets cross-domain unknown-unknown queries of this form.
