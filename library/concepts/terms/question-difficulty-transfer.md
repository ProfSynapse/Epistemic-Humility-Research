---
aliases:
- cross-model difficulty correlation
- difficulty transferability
- surrogate correctness correlation
tags:
- kg/term
- concept
- term
kg:
  id: term:question-difficulty-transfer
  type: term
  status: canonical
area: terms
related:
- '[[2311.08877--llamas-know-what-gpts-dont-show]]'
- '[[surrogate-confidence-estimation]]'
- '[[knowledge-boundary]]'
- '[[verbalized-prob-generalizes-logit-overfits-distribution-shift]]'
- '[[self-knowledge]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[2311.08877--llamas-know-what-gpts-dont-show]]'
  target_id: paper:2311.08877
  confidence: high
- type: related_to
  target: '[[surrogate-confidence-estimation]]'
  target_id: method:surrogate-confidence-estimation
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[verbalized-prob-generalizes-logit-overfits-distribution-shift]]'
  target_id: mechanism:verbalized-prob-generalizes-logit-overfits-distribution-shift
  confidence: medium
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
---

The empirical phenomenon that whether a given question is answered correctly or incorrectly is correlated across different language models, even models of very different architecture, training, and accuracy level. The Pearson correlation between correct-answer indicators for GPT-4 and Llama 2 70B is 0.39 across 12 QA datasets; for Llama 2 13B it falls to 0.19, showing the effect scales with surrogate capacity.

**Why it matters here:** Provides the mechanistic explanation for why surrogate confidence estimation works: a weaker model's probability captures which questions are genuinely hard, because question difficulty is a property of the question and knowledge domain as much as of any one model. This assumption also underpins the Phase 3 abstention-design hypothesis that internal epistemic signals generalize across checkpoints.

**Lineage:** Identified as a core explanation in 2311.08877 Section 6. Related to knowledge-boundary (which concerns a single model's uncertainty limits) and to verbalized-prob-generalizes-logit-overfits-distribution-shift (which concerns generalization of confidence signals across distributions).
