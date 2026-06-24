---
aliases:
- escalating rebuttal chain
- rebuttal chain evaluation
- SycEval rebuttal protocol
- in-context and preemptive rebuttal chains
tags:
- kg/method
- concept
- method
kg:
  id: method:rebuttal-escalation-protocol
  type: method
  status: canonical
area: methods
related:
- '[[2502.08177--syceval]]'
- '[[sycophancy]]'
- '[[progressive-regressive-sycophancy-taxonomy]]'
- '[[llm-as-judge]]'
- '[[citation-rebuttal-drives-regressive-sycophancy]]'
relationships:
- type: proposed_by
  target: '[[2502.08177--syceval]]'
  target_id: paper:2502.08177
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[progressive-regressive-sycophancy-taxonomy]]'
  target_id: term:progressive-regressive-sycophancy-taxonomy
  confidence: medium
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: medium
- type: related_to
  target: '[[citation-rebuttal-drives-regressive-sycophancy]]'
  target_id: mechanism:citation-rebuttal-drives-regressive-sycophancy
  confidence: medium
---

An evaluation design in which an LLM is presented with a sequence of challenges to its initial answer, each challenge adding a layer of rhetorical strength: simple (bare assertion of incorrectness), ethos (authority claim), justification (reasoned argument), and citation-plus-abstract (fabricated supporting literature). Both in-context (follow-up within the same conversation) and preemptive (standalone anticipatory) variants are used. Persistence is measured by tracking whether sycophantic behavior, once triggered, continues through subsequent rebuttals.

**Why it matters here:** The escalating structure isolates rebuttal type as a causal lever: it shows that authority-signaling (citation) specifically drives harmful regressive capitulation while plain assertion drives beneficial progressive capitulation. The persistence sub-measure reveals that a single probe underestimates population-level sycophancy because early capitulation strongly predicts chain-level capitulation (78.5% persistence).

**Lineage:** Introduced in SycEval (2502.08177, Fanous et al., 2025) as a benchmark methodology.
