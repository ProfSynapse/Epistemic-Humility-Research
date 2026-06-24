---
aliases:
- popularity-memorization correlation
- subject popularity predicts LM accuracy
- entity frequency drives factual recall
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:entity-popularity-predicts-parametric-memorization
  type: mechanism
  status: canonical
cause: "Higher subject entity web popularity (Wikipedia page views) in the input question"
effect: "Higher LM accuracy on the corresponding factual QA question across models and relationship types"
polarity: increases
related:
- '[[2212.10511--popqa-when-not-to-trust]]'
- '[[knowledge-boundary]]'
- '[[hallucination]]'
- '[[popqa]]'
- '[[scaling-fails-on-long-tail-knowledge]]'
relationships:
- type: supported_by
  target: '[[2212.10511--popqa-when-not-to-trust]]'
  target_id: paper:2212.10511
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
- type: related_to
  target: '[[scaling-fails-on-long-tail-knowledge]]'
  target_id: mechanism:scaling-fails-on-long-tail-knowledge
  confidence: high
---

Entity popularity measured by Wikipedia monthly page views correlates positively with LM accuracy at the per-question level, with Pearson r roughly 0.4 for GPT-3 davinci-003 and roughly 0.1 for GPT-Neo 1.3B. The correlation holds across 16 relationship types and becomes stronger at larger model scale, indicating that large models have a sharper rather than broader knowledge boundary. Questions about the 4,000 least-popular entities cluster near 15-19% accuracy regardless of model size, while scaling provides clear gains on high-popularity questions.
