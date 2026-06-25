---
aliases:
- computational buffer
- compute buffer effect
- content-independent computation
tags:
- kg/term
- concept
- term
kg:
  id: term:computational-buffer-effect
  type: term
  status: canonical
area: terms
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[factual-priming]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
  target_id: paper:2603.09906
  confidence: high
- type: related_to
  target: '[[factual-priming]]'
  target_id: term:factual-priming
  confidence: high
---

A content-independent mechanism by which a reasoning model uses the act of generating extra reasoning tokens to perform additional latent computation before committing to an answer, bypassing the depth limit of a single forward pass. The benefit comes from the token budget itself, not from the semantic content of the trace: even meaningless filler traces ("Let me think." repeated) raise recall.

**Why it matters here:** It shows part of reasoning's factual-recall benefit is mechanical rather than informational, which complicates interpreting a reasoning model's chain of thought as a faithful account of how it reached an answer. The effect is bounded and non-monotonic (it saturates then reverses past an optimal length), so it cannot fully explain reasoning gains and is not a reliable control signal.

**Lineage:** Extends the filler/pause-token line (Goyal et al., 2024) into modern reasoning LLMs and the parametric-recall setting; contrasts with the content-dependent [[factual-priming]] mechanism.
