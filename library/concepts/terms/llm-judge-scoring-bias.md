---
aliases:
- LLM-as-judge bias
- LLM judge bias
- evaluator scoring bias
- judge scoring bias
tags:
- kg/term
- concept
- term
kg:
  id: term:llm-judge-scoring-bias
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[llm-as-judge]]'
- '[[linear-bias-subspace-hypothesis]]'
relationships:
- type: studied_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: high
- type: related_to
  target: '[[linear-bias-subspace-hypothesis]]'
  target_id: term:linear-bias-subspace-hypothesis
  confidence: medium
---

LLM judge scoring bias is a systematic score change caused by surface framing that is irrelevant to the candidate answer's factual content or logical structure. Examples include stated prestige, verbosity, social consensus, authority cues, sentiment, metacognitive refinement claims, and social-identity framing.

**Why it matters here:** Bias in [[llm-as-judge]] evaluations can distort benchmark conclusions and reward signals even when the judged answer has not materially changed.

**Lineage:** Xu et al. connect the input-output bias literature to the [[linear-bias-subspace-hypothesis]] by testing whether cue-induced score failures have a compact internal geometry.
