---
aliases:
- CNN/DailyMail
- CNNDM
- CNN DailyMail
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:cnn-dailymail-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[2310.06452--rlhf-generalisation-diversity]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
- '[[tldr-dataset]]'
- '[[reward-model]]'
relationships:
- type: proposed_by
  target: '[[2310.06452--rlhf-generalisation-diversity]]'
  target_id: paper:2310.06452
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[tldr-dataset]]'
  target_id: dataset:tldr-dataset
  confidence: medium
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
---

A dataset of news articles paired with human-written abstractive summaries, drawn from CNN and DailyMail news archives. Used as the OOD summarisation test set in Kirk et al. (2023) to probe generalisation from reddit-post summarisation (TL;DR) to news-article summarisation.

**Why it matters here:** Its domain mismatch with TL;DR creates a hard OOD generalisation shift that reveals differential degradation of SFT vs RLHF vs BoN policies, and tests reward-model OOD robustness.

**Lineage:** Introduced by Nallapati et al. (2016); used as OOD evaluation target in Stiennon et al. (2022) and Kirk et al. (2023) (arXiv 2310.06452).
