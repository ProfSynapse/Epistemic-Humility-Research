---
aliases:
- Claude Opus 4.6
tags:
- kg/model
- concept
- model
kg:
  id: model:claude-opus-4-6
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

Claude Opus 4.6 is Anthropic's newest large-scale production language model as
of 2026, cited in "Verbalizable Representations Form a Global Workspace in
Language Models" as one of the models on which the paper's headline findings
are corroborated, without being the subject of a dedicated per-model figure.

**Why it matters here:** it is the most capable model mentioned in the study,
used to check that the [[global-workspace]] finding is not an artifact of a
single model checkpoint.

**Lineage:** part of Anthropic's Claude 4.x model family; no public parameter
count.
