---
aliases:
- IDKHA
- Human-assessed IDK score
- Human-judged contextual abstention
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:idk-human-assessment
  type: metric
  status: canonical
area: metrics
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[abstention-rate]]'
relationships:
- type: proposed_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: high
---

IDK human assessment is a binary human judgment that requires both an explicit
acknowledgment of missing knowledge and semantic grounding in the input query.
The reported score averages these judgments over evaluated responses.

**Why it matters here:** It distinguishes a context-aware acknowledgment of
ignorance from generic refusal, guessing, or a string detector's missed
paraphrase.

**Lineage:** It is a stricter, response-level variant of an
[[abstention-rate]] measure.
