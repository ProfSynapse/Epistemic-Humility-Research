---
aliases:
- GPT-J-6B
- gpt-j
- GPT-J
tags:
- kg/model
- concept
- model
kg:
  id: model:gpt-j-6b
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[gpt-2-xl]]'
- '[[factual-association-recall-mechanism]]'
- '[[subject-enrichment]]'
relationships:
- type: related_to
  target: '[[gpt-2-xl]]'
  target_id: model:gpt-2-xl
- type: related_to
  target: '[[factual-association-recall-mechanism]]'
  target_id: term:factual-association-recall-mechanism
- type: related_to
  target: '[[subject-enrichment]]'
  target_id: term:subject-enrichment
---

GPT-J-6B is a 6B-parameter autoregressive decoder-only language model with 28 transformer layers, introduced by Wang and Komatsuzaki (2021) and released by EleutherAI. It was trained on the Pile, a large diverse text corpus, and provides a second architectural scale point for mechanistic analysis alongside [[gpt-2-xl]].

**Why it matters here:** GPT-J-6B is used for cross-architecture validation of [[factual-association-recall-mechanism]] findings, confirming that [[subject-enrichment]] and upper-attention-head attribute extraction are not artifacts of a single model family but are consistent structural patterns across decoder-only LMs.

**Lineage:** complementary to [[gpt-2-xl]] in mechanistic interpretability studies; both are predecessor open-weight models predating the Llama / Qwen generation used in the locked training-regimen study training experiments.
