---
aliases:
- Excessive decomposability penalty strength degrades reconstruction without atomicity gain
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:overpenalization-degrades-reconstruction
  type: mechanism
  status: canonical
cause: "High [[decomposability-penalty]] strength (lambda=1.0) forcing [[sparse-autoencoder]] decoder directions apart regardless of semantic structure"
effect: "Severe reconstruction quality degradation without commensurate mean |φ| reduction, yielding poor Pareto tradeoffs between atomicity and reconstruction"
polarity: decreases
related:
- '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
- '[[decomposability-penalty]]'
- '[[sparse-autoencoder]]'
relationships:
- type: supported_by
  target: '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
  target_id: paper:2604.03436
  confidence: high
- type: related_to
  target: '[[decomposability-penalty]]'
  target_id: method:decomposability-penalty
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

When the MetaSAE decomposability penalty is set too high (lambda=1.0), decoder directions are pushed apart even when the corresponding features encode semantically related concepts, forcing the model to sacrifice reconstruction accuracy. The MetaSAE paper (arXiv:2604.03436) shows that at this extreme strength the mean |φ| co-occurrence reduction does not improve beyond moderate penalty levels, so reconstruction loss increases sharply with no commensurate atomicity gain. Intermediate penalty strengths occupy the Pareto frontier, implying that the penalty must be tuned to respect the semantic structure of the underlying concepts.
