---
aliases:
- GPT-2
- GPT-2 1558M
- GPT-2 small
- GPT-2 large
tags:
- kg/model
- concept
- model
kg:
  id: model:gpt-2
  type: model
  status: canonical
area: language-models
related:
- '[[gpt-2-xl]]'
- '[[logit-lens]]'
relationships:
- type: related_to
  target: '[[gpt-2-xl]]'
  target_id: model:gpt-2-xl
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
---

GPT-2 is a family of autoregressive, decoder-only transformer language models
introduced by OpenAI (Radford et al., 2019), available in four sizes from 117M
to 1558M parameters and trained on WebText, a filtered dataset of outbound Reddit
links. Each variant stacks transformer blocks with multi-head self-attention and
feed-forward sub-layers over a shared token vocabulary, producing a probability
distribution over the next token at each position. The family established that
scale and data quality jointly drive zero-shot transfer across diverse language
tasks.

**Why it matters here:** GPT-2 is the primary demonstration vehicle for the
[[logit-lens]] analysis: decoding intermediate residual-stream states through
the final unembedding matrix reveals how prediction converges layer by layer,
and [[kl-divergence]] between those decoded distributions and the final output
distribution quantifies the convergence trajectory.

**Lineage:** [[gpt-2-xl]] (1.5B) is the largest member of the same family and
the main subject of mechanistic-interpretability studies building on the logit-lens
framing.
