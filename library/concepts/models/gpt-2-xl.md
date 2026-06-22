---
aliases:
- gpt2-xl
- GPT-2 XL
tags:
- kg/model
- concept
- model
kg:
  id: model:gpt-2-xl
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[gpt-j-6b]]'
- '[[factual-association-recall-mechanism]]'
- '[[logit-lens]]'
relationships:
- type: related_to
  target: '[[gpt-j-6b]]'
  target_id: model:gpt-j-6b
- type: related_to
  target: '[[factual-association-recall-mechanism]]'
  target_id: term:factual-association-recall-mechanism
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
---

GPT-2 XL is a 1.5B-parameter autoregressive decoder-only language model with 48 transformer layers, introduced by Radford et al. (2019) as the largest variant of the GPT-2 family. It was trained on WebText, a filtered crawl of outbound links from Reddit. The model has been widely adopted as a mechanistic-interpretability benchmark because its relatively transparent residual-stream dynamics respond well to probing and causal intervention methods.

**Why it matters here:** GPT-2 XL serves as the primary analysis subject in several foundational mech-interp studies on factual recall, knowledge neurons, and logit-lens trajectories, making its architecture a reference point for understanding where and how factual knowledge is stored.

**Lineage:** contemporaneous with [[gpt-j-6b]], which is used for cross-architecture validation of [[factual-association-recall-mechanism]] findings.
