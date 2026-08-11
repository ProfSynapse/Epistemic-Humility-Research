---
aliases:
- CircuitKIT faithfulness panel
- multi-pillar circuit evaluation
- six-pillar circuit evaluation
tags:
- kg/method
- concept
- method
kg:
  id: method:multi-pillar-circuit-evaluation
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[circuitkit]]'
- '[[circuit-faithfulness]]'
- '[[jaccard-index]]'
- '[[spearman-rank-correlation]]'
relationships:
- type: proposed_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[circuitkit]]'
  target_id: method:circuitkit
  confidence: high
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
  confidence: high
- type: related_to
  target: '[[jaccard-index]]'
  target_id: metric:jaccard-index
  confidence: high
- type: related_to
  target: '[[spearman-rank-correlation]]'
  target_id: metric:spearman-rank-correlation
  confidence: high
---

Multi-pillar circuit evaluation assesses a discovered circuit through causal patching, hard-ablation sufficiency, resample stability, corruption robustness, size-matched baselines, and cross-task generalization. CircuitKIT reports each diagnostic separately because ablation choices and intervention operators can make apparently similar circuits diverge.

**Why it matters here:** This is a strong evaluation contract for epistemic-humility circuits, where a readable direction or reproducible ranking should not count as a mechanism without causal sufficiency, specificity controls, stability, and held-out transfer.

**Lineage:** Extends the single-score [[circuit-faithfulness]] view into a panel that also uses [[jaccard-index]] and [[spearman-rank-correlation]] for stability.
