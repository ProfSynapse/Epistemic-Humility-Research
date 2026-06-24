---
title: 'interpreting GPT: the logit lens'
tags:
- kg/paper
- paper
- epistemic-humility
- mechanistic-interpretability
kg:
  id: paper:ll2020
  type: paper
  status: canonical
year: 2020
url: https://www.lesswrong.com/posts/AcKRB8wDpdaN6v6ru/interpreting-gpt-the-logit-lens
area: mechanistic-interpretability
status: fetched
source: blog
source_kind: lesswrong
authors:
- nostalgebraist
models: []
metrics: []
fulltext: ../fulltext/ll2020--interpreting-gpt-the-logit-lens.html
provenance: 'Awesome-MI ingest batch 2 2026-06-19: non-arxiv source; prose extracted from page HTML into fulltext/. Not in manifest.yaml (arxiv-keyed).'
evaluates:
- '[[gpt-2]]'
related:
- '[[logit-lens]]'
- '[[input-discarding]]'
- '[[unembedding-matrix]]'
- '[[kl-divergence]]'
- '[[residual-stream]]'
- '[[iterative-refinement-transformers]]'
- '[[residual-connections-preserve-basis]]'
- '[[gpt-input-discarded-immediately]]'
- '[[layers-converge-to-output-distribution]]'
relationships:
- type: proposes
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: proposes
  target: '[[input-discarding]]'
  target_id: term:input-discarding
- type: uses
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: uses
  target: '[[unembedding-matrix]]'
  target_id: term:unembedding-matrix
- type: measures
  target: '[[kl-divergence]]'
  target_id: metric:kl-divergence
- type: studies
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: studies
  target: '[[iterative-refinement-transformers]]'
  target_id: term:iterative-refinement-transformers
- type: supports
  target: '[[residual-connections-preserve-basis]]'
  target_id: mechanism:residual-connections-preserve-basis
- type: supports
  target: '[[gpt-input-discarded-immediately]]'
  target_id: mechanism:gpt-input-discarded-immediately
- type: supports
  target: '[[layers-converge-to-output-distribution]]'
  target_id: mechanism:layers-converge-to-output-distribution
proposes: ["[[logit-lens]]", "[[input-discarding]]"]
uses-method: ["[[logit-lens]]", "[[unembedding-matrix]]"]
measures: ["[[kl-divergence]]"]
evaluates: ["[[gpt-2]]"]
studies: ["[[residual-stream]]", "[[iterative-refinement-transformers]]"]
mechanisms: ["[[residual-connections-preserve-basis]]", "[[gpt-input-discarded-immediately]]", "[[layers-converge-to-output-distribution]]"]
---
## Abstract

<!-- non-arxiv source; see fulltext/ for full prose -->

## Summary

<!-- filled during extraction -->

## Relevance to experiment

<!-- mech-interp of features/superposition; Phase 3 probing context -->

## Claims

- Applying the unembedding matrix W^T to intermediate layer activations of GPT-2 yields interpretable probability distributions over the vocabulary, showing that GPT operates in a shared embedding basis across all layers. (Overview section; logit lens plots on GPT-2 1558M) [[logit-lens]]
- After the very first transformer layer, GPT-2's residual stream is already closer to the final output distribution than to the input distribution, indicating that input representations are discarded discontinuously rather than gradually refined. (KL divergence plots, 'KL divergence and input discarding' and 'addendum: more on input discarding' sections) [[input-discarding]]
- By the middle layers, GPT-2 has formed a 'pretty good guess' at the next token: the final top-1 prediction is typically ranked in the top-3 to top-10 candidates, even when the probability ordering has not yet converged. ('ranks' section; rank heatmap figures for GPT-3 abstract example) [[iterative-refinement-transformers]]
- Residual connections (x + f(x)) combined with weight decay explain why the logit lens works: the residual network preserves the same vector-space basis across layers, so the unembedding matrix applied mid-network remains meaningful. ('why? / is this surprising?' section, points 1 and 2) [[residual-stream]]
