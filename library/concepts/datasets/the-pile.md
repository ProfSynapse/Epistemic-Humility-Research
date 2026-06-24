---
aliases:
- The Pile
- PILE dataset
- Pile dataset
- EleutherAI Pile
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:the-pile
  type: dataset
  status: canonical
area: datasets
related:
- '[[2311.13240--calibration-of-llms-and-alignment]]'
- '[[tc2023--towards-monosemanticity]]'
- '[[t-rex]]'
- '[[mmlu]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2311.13240--calibration-of-llms-and-alignment]]'
  target_id: paper:2311.13240
  confidence: high
- type: related_to
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
- type: related_to
  target: '[[t-rex]]'
  target_id: dataset:t-rex
  confidence: medium
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
---

An 800GB curated English text corpus assembled by EleutherAI (Gao et al., 2020) for large language model pretraining, combining 22 diverse data sources including books, academic papers, code, and web text.

**Why it matters here:** The training and evaluation corpus for the Pythia model suite; used in Zhu et al. as the CLM calibration evaluation set, where all Pythia scales achieve ECE below 0.1, establishing a pretraining calibration baseline. It is also the activation source in the sparse-autoencoder interpretability work: a one-layer transformer was trained on The Pile and the autoencoder was then trained on 8 billion token-level activation samples drawn from the same corpus. Knowing which corpus underlies a studied model is essential for interpreting its calibration and abstention behavior.

**Lineage:** Released by Gao et al. (2020) from EleutherAI as an open pretraining resource; underpins the Pythia scaling suite and serves as the activation source in [[tc2023--towards-monosemanticity]].
