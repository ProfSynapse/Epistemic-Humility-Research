---
aliases:
- self-probe premium gap
- privileged-knowledge premium
- self minus best external AUC
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:premium-gap
  type: metric
  status: canonical
area: metrics
related:
- '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
- '[[self-vs-peer-correctness-probing]]'
- '[[privileged-correctness-knowledge]]'
relationships:
- type: proposed_by
  target: '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
  target_id: paper:2604.12373
  confidence: high
- type: measures
  target: '[[privileged-correctness-knowledge]]'
  target_id: term:privileged-correctness-knowledge
  confidence: high
- type: used_by
  target: '[[self-vs-peer-correctness-probing]]'
  target_id: method:self-vs-peer-correctness-probing
  confidence: high
---

The premium gap is the target model's self-probe AUC minus the highest AUC achieved by an external-model probe for the same target correctness labels. A positive gap on target-source disagreement items indicates that the target representation retains predictive information not matched by the tested peer representations.
