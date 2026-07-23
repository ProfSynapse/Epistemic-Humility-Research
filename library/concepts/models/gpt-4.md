---
aliases:
- GPT4
- gpt4
- GPT-4 (OpenAI 2023)
tags:
- kg/model
- concept
- model
kg:
  id: model:gpt-4
  type: model
  status: canonical
area: models
related:
- '[[2303.08774--gpt4-technical-report]]'
- '[[gpt-3]]'
- '[[instructgpt]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[calibration]]'
- '[[rlhf-degrades-conditional-calibration]]'
relationships:
- type: proposed_by
  target: '[[2303.08774--gpt4-technical-report]]'
  target_id: paper:2303.08774
  confidence: high
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
  confidence: medium
- type: related_to
  target: '[[instructgpt]]'
  target_id: model:instructgpt
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[rlhf-degrades-conditional-calibration]]'
  target_id: mechanism:rlhf-degrades-conditional-calibration
  confidence: medium
---

A large-scale multimodal Transformer developed by OpenAI, pre-trained to predict the next token in a document from image and text inputs, then aligned with RLHF. Architecture details (model size, hardware, training compute) are not disclosed in the technical report. Exhibits human-level performance on several professional and academic benchmarks.

**Why it matters here:** GPT-4 is the primary reference model for the calibration-degradation-under-RLHF finding (Figure 8) and for the over-abstention-vs-safety tradeoff that motivates the locked training-regimen study. Its base-vs-RLHF capability comparison (73.7% vs 74.0%) is used as evidence that alignment cost falls on calibration, not on task accuracy.

**Lineage:** Successor to GPT-3 ([[gpt-3]]) and InstructGPT ([[instructgpt]]). Described in arXiv:2303.08774.
