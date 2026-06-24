---
aliases:
- rarity-precision degradation
- entity frequency effect on FActScore
- rare entity hallucination amplification
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:entity-rarity-degrades-factual-precision
  type: mechanism
  status: canonical
cause: "A topic entity is rare in LM pretraining data (low Wikipedia page-view frequency), causing the model's parametric knowledge about that entity to be sparse or absent"
effect: "The fraction of generated atomic facts supported by an external knowledge source (FActScore) falls substantially; for PerplexityAI with retrieval, relative drops of 50% at the atomic level and 64% at the sentence level are observed comparing the rarest to the most frequent entity buckets"
polarity: decreases
related:
- '[[2305.14251--factscore]]'
- '[[factscore]]'
- '[[hallucination]]'
- '[[knowledge-boundary]]'
- '[[arbitrary-vs-systematic-facts]]'
- '[[factscore-biography-benchmark]]'
relationships:
- type: supported_by
  target: '[[2305.14251--factscore]]'
  target_id: paper:2305.14251
  confidence: high
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: high
- type: related_to
  target: '[[arbitrary-vs-systematic-facts]]'
  target_id: term:arbitrary-vs-systematic-facts
  confidence: high
- type: related_to
  target: '[[factscore-biography-benchmark]]'
  target_id: dataset:factscore-biography-benchmark
  confidence: high
---

As entity frequency in pretraining data decreases, LMs have less reliable parametric knowledge about those entities and generate a higher proportion of unsupported atomic facts. Retrieval access does not eliminate this effect: PerplexityAI, which uses a commercial search engine, still shows large rarity-driven FActScore drops. This implies that evaluation sets overweighting head entities will yield systematically inflated factuality estimates relative to deployment conditions where tail entities are common.
