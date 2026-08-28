---
aliases:
- Greater-Than
- greater_than
- numerical year-completion task
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:greater-than
  type: dataset
  status: canonical
area: datasets
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[indirect-object-identification]]'
relationships:
- type: used_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[indirect-object-identification]]'
  target_id: dataset:indirect-object-identification
  confidence: medium
---

Greater-Than is a numerical year-completion task used to study the transformer circuit that predicts valid two-digit year continuations. CircuitKIT pairs it with indirect-object identification in its cross-family circuit-discovery study.

**Why it matters here:** It supplies a non-IOI mechanism check, helping distinguish a generally portable circuit workflow from one tuned to a single canonical task.

**Lineage:** Used as a complementary circuit task to [[indirect-object-identification]].
