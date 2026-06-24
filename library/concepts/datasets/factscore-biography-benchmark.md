---
aliases:
- FActScore people biographies
- biography evaluation set
- FActScore benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:factscore-biography-benchmark
  type: dataset
  status: canonical
area: datasets
related:
- '[[2305.14251--factscore]]'
- '[[factscore]]'
- '[[atomic-fact-decomposition]]'
- '[[hallucination]]'
- '[[abstention]]'
- '[[instructgpt]]'
- '[[gpt-4]]'
relationships:
- type: proposed_by
  target: '[[2305.14251--factscore]]'
  target_id: paper:2305.14251
  confidence: high
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
- type: related_to
  target: '[[atomic-fact-decomposition]]'
  target_id: method:atomic-fact-decomposition
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[instructgpt]]'
  target_id: model:instructgpt
  confidence: medium
- type: related_to
  target: '[[gpt-4]]'
  target_id: model:gpt-4
  confidence: medium
---

An evaluation dataset of 183 people entities sampled from Wikidata with corresponding Wikipedia pages, spanning diverse nationalities, professions, and entity-frequency levels (from frequent to rare in pretraining corpora). For each entity, a prompt asking for a biography is issued to a subject LM, and the response is human-annotated at the atomic-fact level (Supported, Not-supported, Irrelevant) against English Wikipedia. Inter-rater agreement on a 10% double-annotated subset is 96%, 90%, and 88% for InstructGPT, ChatGPT, and PerplexityAI respectively.

**Why it matters here:** This is the human-annotated ground truth that establishes the primary reference FActScores (42.5% / 58.3% / 71.5%) against which automated estimators are calibrated, and the entity-frequency stratification is what enables the rarity-degrades-precision finding central to evaluation-set design guidance in this vault.

**Lineage:** Constructed in arXiv:2305.14251, Section 3.3, as part of the FActScore paper; entity sampling drawn from Wikidata with frequency bins defined in Appendix A.1 of that paper.
