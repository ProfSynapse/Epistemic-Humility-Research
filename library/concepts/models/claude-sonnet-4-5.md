---
aliases:
- Claude Sonnet 4.5
tags:
- kg/model
- concept
- model
kg:
  id: model:claude-sonnet-4-5
  type: model
  status: canonical
area: language-models
related:
- '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
- '[[jacobian-lens]]'
- '[[global-workspace]]'
relationships:
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: high
---

Claude Sonnet 4.5 is Anthropic's mid-scale production language model as of
2026 and the primary subject of the "Verbalizable Representations Form a
Global Workspace in Language Models" study, where the [[jacobian-lens]] is
computed and its causal effects (verbal-report swaps, modulation, reasoning
mediation, broadcast, selective ablation) are measured in most depth.

**Why it matters here:** it is the empirical anchor for the paper's
[[global-workspace]] claims; results on Claude Haiku 4.5, Opus 4.5, and Opus
4.6 are reported as corroboration rather than the primary evidence base.

**Lineage:** part of Anthropic's Claude 4.x model family; no public parameter
count.
