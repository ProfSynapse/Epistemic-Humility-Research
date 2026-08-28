---
aliases:
- Circuit Breaker Set
- circuit breaker dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:circuit-breaker-set
  type: dataset
  status: canonical
area: datasets
related:
- '[[2406.04313--improving-alignment-robustness-circuit-breakers]]'
- '[[representation-rerouting]]'
relationships:
- type: proposed_by
  target: '[[2406.04313--improving-alignment-robustness-circuit-breakers]]'
  target_id: paper:2406.04313
  confidence: high
- type: related_to
  target: '[[representation-rerouting]]'
  target_id: method:representation-rerouting
  confidence: high
---

The Circuit Breaker Set contains examples whose responses elicit internal representations associated with harmful generation. The paper pairs it with a Retain Set of benign and refusal examples used to preserve desired representations.

**Why it matters here:** The paired targeted and retain data define where a representation-space objective should change the model and where it should preserve behavior.

**Lineage:** The paper provides text, multimodal, and function-calling variants for Representation Rerouting.
