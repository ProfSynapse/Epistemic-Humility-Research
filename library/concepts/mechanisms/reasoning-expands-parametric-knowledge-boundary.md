---
aliases:
- reasoning expands parametric recall boundary
- reasoning unlocks latent knowledge
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reasoning-expands-parametric-knowledge-boundary
  type: mechanism
  status: canonical
cause: "Enabling a model's reasoning mode (ON) before it answers a single-hop factual question, holding parametric knowledge fixed via a hybrid ON/OFF model."
effect: "pass@k rises consistently over reasoning OFF across models and datasets, often widening with k (nearly doubling for Qwen3-32B on SimpleQA-Verified), surfacing correct answers that were effectively unreachable without reasoning."
polarity: increases
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[knowledge-boundary]]'
- '[[pass-at-k]]'
- '[[generation-discrimination-gap]]'
relationships:
- type: supported_by
  target: '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
  target_id: paper:2603.09906
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
---

Reasoning expands the boundary of parametric knowledge a model can actually express, not just its top-1 accuracy: the reasoning-effectiveness metric Omega is positive across all settings and is larger for weaker models, indicating they hold more hidden knowledge that reasoning unlocks (Figure 1, Figure 2). Question-complexity analysis shows the gain comes from better recall rather than multi-hop decomposition (Figure 3, Section 4).
