---
aliases:
- WinoBias
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:winobias
  type: dataset
  status: canonical
area: datasets
related:
- '[[2410.02707--llms-know-more-than-they-show]]'
- '[[hallucination]]'
- '[[error-type-taxonomy-llm]]'
- '[[exact-answer-token-probing]]'
relationships:
- type: proposed_by
  target: '[[2410.02707--llms-know-more-than-they-show]]'
  target_id: paper:2410.02707
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[error-type-taxonomy-llm]]'
  target_id: term:error-type-taxonomy-llm
  confidence: medium
- type: related_to
  target: '[[exact-answer-token-probing]]'
  target_id: method:exact-answer-token-probing
  confidence: medium
---

A dataset by Zhao et al. (2018) for measuring gender bias in coreference resolution, containing sentences with occupations and pronouns designed to surface stereotypical gender associations. Used in 2410.02707 as one of ten evaluation domains for error-detection probing.

**Why it matters here:** Represents a bias/common-sense reasoning task rather than factual retrieval, making it an important test for whether truthfulness probes trained on factual QA generalize to non-factual error types.

**Lineage:** Zhao et al. 2018. Used as an evaluation dataset in 2410.02707 alongside TriviaQA, Math, Winobias, and others.
