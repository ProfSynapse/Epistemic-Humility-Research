---
aliases:
- Gender Concept Erasure Reduces Downstream TPR-GAP
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gender-erasure-reduces-tpr-gap
  type: mechanism
  status: canonical
cause: Applying [[leace]] to remove gender information from BERT CLS embeddings
effect: TPR-Gap drops from 0.198 to 0.084 in a downstream profession classifier while profession-prediction accuracy falls only from 79.3% to 77.3%, indicating targeted bias reduction with minimal task-utility loss
polarity: decreases
related:
- '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
- '[[leace]]'
- '[[tpr-gap]]'
- '[[bias-in-bios]]'
relationships:
- type: supported_by
  target: '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
  target_id: paper:2306.03819
  confidence: high
- type: related_to
  target: '[[leace]]'
  target_id: method:leace
- type: related_to
  target: '[[tpr-gap]]'
  target_id: metric:tpr-gap
contradicted-by: []
---

When [[leace]] is applied to BERT CLS embeddings on the [[bias-in-bios]] benchmark, the [[tpr-gap]] across professions drops from 0.198 to 0.084 while main-task profession accuracy declines by only 2 percentage points. This demonstrates that gender and occupation signals occupy partially separable linear subspaces, so targeted erasure of the gender direction primarily removes the bias rather than task-relevant signal. The result is reported in arXiv:2306.03819 and positions [[leace]] as a more utility-preserving alternative to [[inlp]] for bias mitigation.
