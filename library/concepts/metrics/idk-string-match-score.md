---
aliases:
- IDKSM
- IDK string-matching score
- Ignorance-expression match rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:idk-string-match-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[abstention-rate]]'
- '[[idk-human-assessment]]'
relationships:
- type: proposed_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: high
- type: related_to
  target: '[[idk-human-assessment]]'
  target_id: metric:idk-human-assessment
  confidence: high
---

IDK string-match score is the fraction of responses containing one of a set of
common ignorance expressions. It can undercount semantically valid abstentions
whose wording is absent from the phrase list.

**Why it matters here:** The paper reports it as an automated companion to
[[idk-human-assessment]], not as a complete measure of epistemic abstention.

**Lineage:** It operationalizes an [[abstention-rate]] with lexical matching.
