---
aliases:
- attention sink
- attention sinks
tags:
- kg/term
- concept
- term
kg:
  id: term:attention-sink
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2402.17762--massive-activations-large-language-models]]'
- '[[massive-activations]]'
- '[[implicit-attention-bias]]'
relationships:
- type: related_to
  target: '[[massive-activations]]'
  target_id: term:massive-activations
  confidence: high
- type: related_to
  target: '[[implicit-attention-bias]]'
  target_id: term:implicit-attention-bias
  confidence: high
- type: studied_by
  target: '[[2402.17762--massive-activations-large-language-models]]'
  target_id: paper:2402.17762
  confidence: high
---

An attention sink is a token that receives a disproportionate share of attention
across queries while contributing little semantic content, originally identified
as the first token (Xiao et al. 2023). Sun et al. generalize sinks to any token
carrying a massive activation and give the mechanistic cause: attention
concentrates on those tokens, whose value vectors are near-identical across
query positions, so the attention output acquires a constant additive term. This
lets the model implement a no-op or bias that avoids over-mixing and
representational collapse in deep residual streams.

**Why it matters here:** attention sinks explain why displacement at special
token positions (the start token, first delimiter) can be large yet carry no
per-item epistemic signal. A census that pools across positions will inherit the
sink signature; conditioning on token type separates it out.

**Lineage:** caused by [[massive-activations]] through an
[[implicit-attention-bias]]; a position/token-type bookkeeping phenomenon rather
than a content feature.
