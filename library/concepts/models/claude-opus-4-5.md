---
aliases:
- Claude Opus 4.5
tags:
- kg/model
- concept
- model
kg:
  id: model:claude-opus-4-5
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

Claude Opus 4.5 is Anthropic's large-scale production language model as of
2026, used as a corroborating model in the "Verbalizable Representations Form
a Global Workspace in Language Models" study, including the
internal-reasoning-mediation experiment (Figure 15, 70% swap success, tied
with Sonnet 4.5) and the directed-modulation scaling comparison (Figure 10).

**Why it matters here:** used alongside Sonnet 4.5 and Haiku 4.5 to show that
J-lens effects generalize across the Claude 4.x model family and to support
the claim that some effect sizes scale with model size.

**Lineage:** part of Anthropic's Claude 4.x model family; no public parameter
count.
