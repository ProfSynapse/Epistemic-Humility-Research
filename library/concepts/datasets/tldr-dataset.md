---
aliases:
- TL;DR
- reddit TL;DR
- Völske TL;DR
- TLDR
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:tldr-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[2310.06452--rlhf-generalisation-diversity]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
- '[[cnn-dailymail-dataset]]'
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
  target: '[[cnn-dailymail-dataset]]'
  target_id: dataset:cnn-dailymail-dataset
  confidence: medium
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
---

A dataset of approximately 120,000 Reddit posts with human-written summary suffixes drawn from the 'Too Long; Didn't Read' (TL;DR) convention, filtered and used by Stiennon et al. (2022) for summarisation training and by Kirk et al. (2023) as the in-distribution summarisation training and test set.

**Why it matters here:** Standard benchmark for RLHF summarisation research; training on TL;DR and evaluating on CNN/DailyMail defines the hard OOD generalisation shift studied in Kirk et al. (2023).

**Lineage:** Introduced by Völske et al. (2017); filtered and used for RLHF research by Stiennon et al. (2022, arXiv 2009.01325); used as in-distribution training/test in Kirk et al. (2023) (arXiv 2310.06452).
