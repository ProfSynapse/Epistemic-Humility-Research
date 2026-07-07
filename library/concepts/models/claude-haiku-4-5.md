---
aliases:
- Claude Haiku 4.5
tags:
- kg/model
- concept
- model
kg:
  id: model:claude-haiku-4-5
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

Claude Haiku 4.5 is Anthropic's small-scale production language model as of
2026, used as a corroborating and ablation-target model in the "Verbalizable
Representations Form a Global Workspace in Language Models" study: it is the
model the flexible-vs-automatic-task ablation (Figure 21, Figure 24) and one
arm of the internal-reasoning-mediation experiment (Figure 15, 54% swap
success) are run on.

**Why it matters here:** its lower reasoning-mediation swap-success rate
relative to Sonnet 4.5 and Opus 4.5 (54% vs. 70%/70%) is cited as evidence that
the effect "tends to increase with model size."

**Lineage:** part of Anthropic's Claude 4.x model family; no public parameter
count.
