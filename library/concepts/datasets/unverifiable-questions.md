---
aliases:
- Unverifiable dataset
- Fictitious unverifiable questions
- Unverifiable questions dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:unverifiable-questions
  type: dataset
  status: canonical
area: datasets
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[abstention]]'
relationships:
- type: used_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
---

The Unverifiable Questions dataset contains 187 GPT-4-generated questions about
fictitious concepts. The evaluated base models were checked to acknowledge
missing knowledge on these questions before adaptation.

**Why it matters here:** It is the main unknown-query set for measuring whether
fine-tuning preserves output-level abstention behavior.
