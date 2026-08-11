---
aliases:
- Intervention Reliability Index
- RI(C)
- circuit intervention reliability
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:intervention-reliability-index
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[multi-pillar-circuit-evaluation]]'
- '[[spearman-rank-correlation]]'
relationships:
- type: proposed_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[multi-pillar-circuit-evaluation]]'
  target_id: method:multi-pillar-circuit-evaluation
  confidence: high
- type: related_to
  target: '[[spearman-rank-correlation]]'
  target_id: metric:spearman-rank-correlation
  confidence: high
---

The Intervention Reliability Index is CircuitKIT's optional seventh diagnostic. It takes the harmonic mean of normalized cross-seed score consistency, downstream effect magnitude, and low relative effect variance, producing an index in [0, 1].

**Why it matters here:** It supplies a preregistrable way to distinguish a circuit intervention that works once from one whose selected components and behavioral effect replicate across re-discovery seeds. CircuitKIT defines the statistic but does not report it at scale in the paper's single-seed intervention studies.

**Lineage:** Proposed as an optional extension to [[multi-pillar-circuit-evaluation]] and uses [[spearman-rank-correlation]] for its seed-consistency component.
