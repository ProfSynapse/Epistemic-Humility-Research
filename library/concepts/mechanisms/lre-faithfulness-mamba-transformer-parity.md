---
aliases:
- LRE faithfulness in Mamba approximates transformer LM parity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:lre-faithfulness-mamba-transformer-parity
  type: mechanism
  status: canonical
cause: Fitting a first-order linear relation embedding (LRE) to Mamba's subject representations at the optimal extraction layer
effect: LRE achieves greater than 50% faithfulness for 10 of 26 factual relations in Mamba-2.8b, compared to 11 of 26 in Pythia-2.8b, indicating similar linearity of factual relation representations across architectures
polarity: enables
related:
- '[[2404.03646--locating-editing-factual-associations-mamba]]'
- '[[linear-relation-embedding]]'
- '[[mamba-ssm]]'
- '[[lre-dataset]]'
relationships:
- type: supported_by
  target: '[[2404.03646--locating-editing-factual-associations-mamba]]'
  target_id: paper:2404.03646
  confidence: high
- type: related_to
  target: '[[linear-relation-embedding]]'
  target_id: method:linear-relation-embedding
- type: related_to
  target: '[[mamba-ssm]]'
  target_id: model:mamba-ssm
- type: related_to
  target: '[[lre-dataset]]'
  target_id: dataset:lre-dataset
---

[[linear-relation-embedding]] (LRE) probes whether factual relations are encoded as approximately linear maps between subject and object representations (arXiv:2404.03646). Applied to [[mamba-ssm]] (2.8b parameters), LRE exceeds 50% faithfulness for 10 of 26 relations, compared to 11 of 26 for the transformer Pythia-2.8b baseline -- a near parity that suggests the linearity of relational representations is an architectural-agnostic property of pretrained language models at this scale. This cross-architecture convergence supports the view that factual knowledge geometry reflects training data statistics more than specific architectural inductive biases.
