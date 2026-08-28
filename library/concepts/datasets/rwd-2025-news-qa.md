---
aliases:
- RWD
- Real-world 2025 news QA dataset
- Post-cutoff Wikinews questions
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:rwd-2025-news-qa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[pistol]]'
- '[[tofu]]'
relationships:
- type: proposed_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: related_to
  target: '[[pistol]]'
  target_id: dataset:pistol
  confidence: medium
- type: related_to
  target: '[[tofu]]'
  target_id: dataset:tofu
  confidence: medium
---

RWD is a question-answer dataset about Wikinews events from January through
June 2025. GPT-4o generated the question-answer pairs, and the events occur
after the stated knowledge cutoffs of the evaluated base models.

**Why it matters here:** It complements synthetic knowledge updates with a
time-based, real-world unknown set.
