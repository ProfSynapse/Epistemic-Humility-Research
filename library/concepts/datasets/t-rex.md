---
aliases:
- T-REx
- TREx
- entity-linking-trex
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:t-rex
  type: dataset
  status: canonical
area: datasets
related:
- '[[2311.13240--calibration-of-llms-and-alignment]]'
- '[[mmlu]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[instruction-tuning]]'
relationships:
- type: proposed_by
  target: '[[2311.13240--calibration-of-llms-and-alignment]]'
  target_id: paper:2311.13240
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: medium
---

A large-scale entity-linking dataset that aligns natural language text from Wikipedia with knowledge base triples (Elsahar et al., 2018). Used to evaluate factual entity prediction calibration by having models generate the first token of entity spans.

**Why it matters here:** Provides a factuality-oriented calibration evaluation task distinct from both CLM and multiple-choice formats; used in Zhu et al. to show that parameter scale has a stronger positive effect on calibration and accuracy for factual knowledge retrieval than for generic text generation.

**Lineage:** Created by Elsahar et al. (2018), presented at LREC 2018. Entity-labeled texts extracted from Wikipedia pages aligned with Wikidata triples.
