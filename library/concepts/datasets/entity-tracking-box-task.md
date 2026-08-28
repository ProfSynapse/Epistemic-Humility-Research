---
aliases:
- entity tracking box task
- synthetic box tracking dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:entity-tracking-box-task
  type: dataset
  status: canonical
area: datasets
related:
- '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
relationships:
- type: used_by
  target: '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
  target_id: paper:2402.14811
  confidence: high
---

The entity-tracking box task describes seven single-token objects placed in lettered boxes and asks the model to complete which object a queried box contains. The paper reorders statements so the query cannot be solved by matching an identical text segment.
