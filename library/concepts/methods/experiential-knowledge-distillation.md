---
aliases:
- Experiential Knowledge Distillation
- experiential knowledge consolidation
tags:
- kg/method
- concept
- method
kg:
  id: method:experiential-knowledge-distillation
  type: method
  status: canonical
area: methods
related:
- '[[2602.12275--policy-context-distillation-language-models]]'
- '[[on-policy-context-distillation]]'
relationships:
- type: proposed_by
  target: '[[2602.12275--policy-context-distillation-language-models]]'
  target_id: paper:2602.12275
  confidence: high
- type: variation_of
  target: '[[on-policy-context-distillation]]'
  target_id: method:on-policy-context-distillation
  confidence: high
---

Experiential knowledge distillation extracts reusable lessons from a model's
historical solution traces, accumulates those lessons in context, and then
distills the context into model parameters. The extraction stage does not use
ground-truth labels in the paper's math and text-game settings.

**Why it matters here:** It tests whether useful context acquired during model
interaction can become persistent weight-level behavior.

**Lineage:** It is an application of [[on-policy-context-distillation]] to
self-generated experience.
