---
aliases:
- Jaccard index
- Jaccard similarity
- Jaccard overlap
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:jaccard-index
  type: metric
  status: canonical
area: metrics
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[spearman-rank-correlation]]'
- '[[multi-pillar-circuit-evaluation]]'
relationships:
- type: measured_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[spearman-rank-correlation]]'
  target_id: metric:spearman-rank-correlation
  confidence: high
- type: related_to
  target: '[[multi-pillar-circuit-evaluation]]'
  target_id: method:multi-pillar-circuit-evaluation
  confidence: high
---

The Jaccard index measures set overlap as the intersection size divided by the union size. In circuit analysis it compares thresholded component sets across discovery seeds, methods, or reference taxonomies.

**Why it matters here:** It distinguishes reproducible component selection from score agreement and gives a direct set-level stability check for proposed epistemic-humility circuits.

**Lineage:** Used alongside [[spearman-rank-correlation]] in [[multi-pillar-circuit-evaluation]].
