---
aliases:
- Real Toxicity Prompts
- RTP
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:realtoxicityprompts
  type: dataset
  status: canonical
area: datasets
related:
- '[[2303.08774--gpt4-technical-report]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[hallucination]]'
- '[[safety-refusal]]'
relationships:
- type: proposed_by
  target: '[[2303.08774--gpt4-technical-report]]'
  target_id: paper:2303.08774
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: medium
---

A dataset of naturally-occurring, potentially toxic web-text sentence starters used to evaluate the tendency of language models to generate toxic continuations. Models are scored by the fraction of prompted completions rated as toxic by a classifier.

**Why it matters here:** Used in the GPT-4 Technical Report to compare GPT-4 (0.73% toxic generation) and GPT-3.5 (6.48%), quantifying the safety benefit of RLHF mitigations. Provides a concrete numeric anchor for the harmful-output side of the safety-calibration tradeoff.

**Lineage:** Introduced by Gehman et al. (2020). Used as a standard safety benchmark across RLHF evaluation work.
