---
aliases:
- LEACE Achieves Perfect Erasure with Minimal Embedding Distortion
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:leace-minimal-distortion-perfect-erasure
  type: mechanism
  status: canonical
cause: Applying the [[leace]] closed-form oblique projection to embeddings
effect: Reduces gender-prediction accuracy to random chance (perfect erasure) with the smallest mean-squared deviation from the original embedding, approximately 2 orders of magnitude faster than [[rlace]] and without gradient-based optimisation
polarity: enables
related:
- '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
- '[[leace]]'
- '[[rlace]]'
- '[[linear-concept-erasure]]'
relationships:
- type: supported_by
  target: '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
  target_id: paper:2306.03819
  confidence: high
- type: related_to
  target: '[[leace]]'
  target_id: method:leace
- type: related_to
  target: '[[rlace]]'
  target_id: method:rlace
contradicted-by: []
---

[[leace]] derives a closed-form oblique projection that simultaneously guarantees linear concept erasure (the concept is unrecoverable by any linear classifier) and minimises mean-squared distortion to the original representation. Because the solution is analytic, it requires no gradient-based optimisation and runs roughly two orders of magnitude faster than [[rlace]], while achieving comparable or better task-utility preservation. arXiv:2306.03819 proves this optimality analytically and validates it empirically on gender erasure from BERT embeddings.
