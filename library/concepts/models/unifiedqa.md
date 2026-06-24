---
aliases:
- UnifiedQA-11B
- UnifiedQA-T5
- unified-qa
tags:
- kg/model
- concept
- model
kg:
  id: model:unifiedqa
  type: model
  status: canonical
area: models
related:
- '[[2009.03300--mmlu-benchmark]]'
- '[[mmlu]]'
- '[[gpt-3]]'
- '[[in-context-learning]]'
relationships:
- type: proposed_by
  target: '[[2009.03300--mmlu-benchmark]]'
  target_id: paper:2009.03300
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
  confidence: medium
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: medium
---

A T5-based question-answering model finetuned by Khashabi et al. on a diverse collection of NLP QA datasets (including SQuAD, NaturalQuestions, ARC, and others) to answer questions uniformly across multiple formats (extractive, abstractive, multiple-choice, yes/no). It is not finetuned on MMLU but transfers zero-shot to the benchmark.

**Why it matters here:** UnifiedQA at 11B parameters outperforms GPT-3 at 175B (48.9% vs 43.9% MMLU overall), demonstrating that supervised exposure to diverse QA formats is a potent substitute for raw scale when evaluating multitask academic knowledge. This result anchors the claim that training distribution and format coverage matter as much as parameter count for knowledge benchmarks.

**Lineage:** Built on T5 by Khashabi et al. (arXiv:2005.00700); related to other T5-based QA models and to the GPT-3 family as a scale comparison point.
