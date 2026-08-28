---
aliases:
- World Affecting
- World Affecting dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:world-affecting
  type: dataset
  status: canonical
area: datasets
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[tiny-mmlu]]'
relationships:
- type: related_to
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: related_to
  target: '[[tiny-mmlu]]'
  target_id: dataset:tiny-mmlu
  confidence: medium
---

World Affecting is a multiple-choice evaluation dataset of generated scenarios with an ethical action and an evil action. The paper uses it to test whether an evil weight direction learned from open-ended personal-advice data generalizes to a different task and answer format.

**Why it matters here:** It supplies an out-of-distribution behavioral-control test paired with a capability check on [[tiny-mmlu]].

**Lineage:** Introduced by Kei et al. (2024) and reused by Fierro and Roger.
