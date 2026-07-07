---
aliases:
- model working memory
- internal cognitive space
- working memory for intermediate variables
tags:
- kg/term
- concept
- term
kg:
  id: term:cognitive-space
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[global-workspace]]'
- '[[jacobian-lens]]'
- '[[residual-stream]]'
- '[[linear-representation-hypothesis]]'
- '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
relationships:
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
  confidence: medium
- type: related_to
  target: '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
  target_id: paper:tc-2026-workspace-commentary-nanda
  confidence: high
---

Cognitive space is Neel Nanda's term for a model-internal working memory where intermediate variables are stored during a forward pass. In this framing, [[jacobian-lens]] is not identical to the cognitive space; it is an approximate method for accessing the portion of that space aligned with verbalizable token directions.

**Why it matters here:** the term captures the actuation-relevant hypothesis behind J-space without committing to the philosophy of global workspace theory. It asks whether doubt, uncertainty, or abstention-relevant variables live in a shared internal workspace that can be read and perhaps written.

**Lineage:** articulated in Nanda's commentary as a first-principles explanation for why J-lens can expose intermediate variables and why it should outperform a simple [[logit-lens]] on multi-step computation.
