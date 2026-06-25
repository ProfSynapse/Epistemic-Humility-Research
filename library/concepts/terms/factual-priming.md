---
aliases:
- factual priming
- generative self-retrieval
tags:
- kg/term
- concept
- term
kg:
  id: term:factual-priming
  type: term
  status: canonical
area: terms
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[computational-buffer-effect]]'
- '[[generation-discrimination-gap]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
  target_id: paper:2603.09906
  confidence: high
- type: related_to
  target: '[[computational-buffer-effect]]'
  target_id: term:computational-buffer-effect
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
---

A content-dependent mechanism in which a reasoning model performs generative self-retrieval: by recalling topically related facts during reasoning, it builds a contextual bridge that lowers the threshold for retrieving the correct answer, analogous to spreading activation in human semantic memory (Collins and Loftus, 1975). Extracting the recalled facts and re-prompting with reasoning disabled recovers most of the pass@k gain, showing the facts themselves carry the benefit.

**Why it matters here:** It is a concrete account of how a model can surface latent knowledge it would otherwise fail to express, directly relevant to the generation-discrimination gap and to whether training expands or suppresses accessible knowledge. The mechanism is fragile: the self-generated facts can be hallucinated, and wrong intermediate facts propagate into wrong final answers.

**Lineage:** Contrasts with the content-independent [[computational-buffer-effect]]; connects to the [[generation-discrimination-gap]] (knowledge encoded but not generated) and the [[knowledge-boundary]] literature.
