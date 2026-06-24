---
aliases:
- Bird
- Bird dataset
- BIRD
- Bird SQL
- BIRD benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:bird-sql-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
- '[[dph-rl]]'
- '[[pass-at-k]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: proposed_by
  target: '[[2509.07430--choice-of-divergence-rlvr-diversity]]'
  target_id: paper:2509.07430
  confidence: high
- type: related_to
  target: '[[dph-rl]]'
  target_id: method:dph-rl
  confidence: medium
- type: related_to
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
---

A large-scale text-to-SQL benchmark containing complex natural-language questions paired with SQL queries over real-world databases. It is used as the in-domain training and evaluation set for SQL tasks in DPH-RL experiments; Spider serves as the corresponding out-of-domain SQL evaluation set.

**Why it matters here:** Provides the in-domain SQL training signal for DPH-RL experiments; performance on Bird (Greedy, Pass@8, Pass@16) and generalization to Spider together reveal whether mass-covering divergence preserves OOD SQL capability alongside in-domain accuracy gains.

**Lineage:** Standard SQL reasoning benchmark used alongside Spider for OOD transfer evaluation in the DPH-RL experimental suite.
