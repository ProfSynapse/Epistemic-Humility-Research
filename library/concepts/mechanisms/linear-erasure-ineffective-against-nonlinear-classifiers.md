---
aliases:
- Linear concept erasure does not prevent non-linear classifiers from recovering the concept
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:linear-erasure-ineffective-against-nonlinear-classifiers
  type: mechanism
  status: canonical
cause: "[[rlace]] erasing only the linear subspace encoding a concept, leaving non-linear structure intact in the remaining representation"
effect: "Non-linear classifiers (RBF-SVM, ReLU MLP) can still predict binary gender with >90% accuracy after rank-1 RLACE projection"
polarity: prevents
related:
- '[[2201.12091--linear-adversarial-concept-erasure]]'
- '[[rlace]]'
- '[[linear-concept-erasure]]'
- '[[linear-guardedness]]'
relationships:
- type: supported_by
  target: '[[2201.12091--linear-adversarial-concept-erasure]]'
  target_id: paper:2201.12091
  confidence: high
- type: related_to
  target: '[[rlace]]'
  target_id: method:rlace
- type: related_to
  target: '[[linear-guardedness]]'
  target_id: term:linear-guardedness
contradicted-by: []
---

[[rlace]] is designed to achieve [[linear-guardedness]]: no linear classifier can recover the erased concept above chance after the projection. However, this guarantee does not extend to non-linear probes -- RBF-SVM and ReLU MLP classifiers still achieve over 90% gender-prediction accuracy on RLACE-projected BERT representations, because non-linear structure encoding the concept survives in the remaining dimensions. arXiv:2201.12091 reports this explicitly, clarifying that linear erasure is a strictly weaker guarantee than full concept removal.
