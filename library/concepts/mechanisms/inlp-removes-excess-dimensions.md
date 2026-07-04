---
aliases:
- INLP removes more dimensions than necessary to erase a concept
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:inlp-removes-excess-dimensions
  type: mechanism
  status: canonical
cause: "[[inlp]]'s sequential nullspace-projection procedure for logistic regression classifiers"
effect: "INLP requires many more projection directions (K>1) than [[rlace]] to approach chance accuracy, unnecessarily damaging representational utility"
polarity: increases
related:
- '[[2201.12091--linear-adversarial-concept-erasure]]'
- '[[inlp]]'
- '[[rlace]]'
- '[[linear-concept-erasure]]'
relationships:
- type: supported_by
  target: '[[2201.12091--linear-adversarial-concept-erasure]]'
  target_id: paper:2201.12091
  confidence: high
- type: related_to
  target: '[[inlp]]'
  target_id: method:inlp
- type: related_to
  target: '[[rlace]]'
  target_id: method:rlace
contradicted-by: []
---

Because [[inlp]] iteratively removes the nullspace of a fresh logistic regression classifier at each round, it overshoots the minimal erasure subspace: the classifiers at successive rounds are not adversarially optimal, so multiple directions must be removed to approximate what [[rlace]] achieves in one rank-1 step. The excess removal degrades downstream task utility more than necessary. arXiv:2201.12091 demonstrates this gap empirically, showing INLP needs substantially more iterations than RLACE to reduce gender accuracy to chance while incurring greater representation distortion.
