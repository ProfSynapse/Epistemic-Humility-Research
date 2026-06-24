---
aliases:
- SICs
- SIC schema
- ignorance certificates
tags:
- kg/method
- concept
- method
kg:
  id: method:structured-ignorance-certificates
  type: method
  status: canonical
area: methods
related:
- '[[2606.08571--structured-ignorance-certificates]]'
- '[[group-relative-policy-optimization]]'
- '[[sic-composite-reward]]'
- '[[paraphrase-divergence-probe]]'
- '[[unknown-unknown-dataset]]'
- '[[abstention-generalization-failure]]'
- '[[knowledge-boundary]]'
- '[[hallucination]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2606.08571--structured-ignorance-certificates]]'
  target_id: paper:2606.08571
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[sic-composite-reward]]'
  target_id: method:sic-composite-reward
  confidence: medium
- type: related_to
  target: '[[paraphrase-divergence-probe]]'
  target_id: method:paraphrase-divergence-probe
  confidence: medium
- type: related_to
  target: '[[unknown-unknown-dataset]]'
  target_id: dataset:unknown-unknown-dataset
  confidence: medium
- type: related_to
  target: '[[abstention-generalization-failure]]'
  target_id: mechanism:abstention-generalization-failure
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A JSON-formatted output schema that requires a model to explicitly name the missing domain intersection for a query it cannot answer, enumerate the concepts it would need, and propose a productive retrieval query rather than hallucinating an answer. Trained via GRPO with a composite reward.

**Why it matters here:** Converts the unknown-unknown failure mode from silent hallucination into a structured, machine-readable epistemic declaration that downstream retrieval systems can act on.

**Lineage:** Introduced in Sahoo 2026 (arXiv 2606.08571) as an alternative to abstention-only training for queries beyond single-domain knowledge boundaries.
