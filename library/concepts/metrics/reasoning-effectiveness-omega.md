---
aliases:
- Reasoning Effectiveness
- Omega metric
- Reasoning Effectiveness (Omega)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:reasoning-effectiveness-omega
  type: metric
  status: canonical
area: metrics
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[pass-at-k]]'
relationships:
- type: proposed_by
  target: '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
  target_id: paper:2603.09906
  confidence: high
- type: related_to
  target: '[[pass-at-k]]'
  target_id: metric:pass-at-k
  confidence: high
---

A single summary metric (denoted Omega) that aggregates the relative percentage difference in pass@k between reasoning ON and OFF across all k from 1 to N, using a linear weight k so that larger k values count more. It scores how much reasoning expands a model's capability boundary rather than just its top-1 accuracy.

**Why it matters here:** Omega turns a full pass@k curve into one comparable number, so reasoning's effect on parametric recall can be ranked across models and datasets. The paper finds Omega decreases as base model capability increases, meaning weaker models have more hidden knowledge that reasoning unlocks.

**Lineage:** Built on the [[pass-at-k]] coverage metric (Yue et al., 2025; unbiased estimator from Chen, 2021); the ON-vs-OFF weighting is introduced by this paper.
