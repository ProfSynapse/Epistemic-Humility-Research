---
aliases:
- Knowledge Neurons Concentrate in Upper Transformer Layers
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-neurons-concentrated-upper-layers
  type: mechanism
  status: canonical
cause: Factual relational knowledge representation in pretrained Transformers
effect: Knowledge neurons identified by the attribution method are predominantly distributed in the topmost FFN layers of BERT, not the lower layers
polarity: enables
related:
- '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
- '[[knowledge-neurons]]'
- '[[knowledge-attribution]]'
relationships:
- type: supported_by
  target: '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
  target_id: paper:2104.08696
  confidence: high
- type: related_to
  target: '[[knowledge-neurons]]'
  target_id: term:knowledge-neurons
- type: related_to
  target: '[[knowledge-attribution]]'
  target_id: method:knowledge-attribution
---

Applying the [[knowledge-attribution]] integrated-gradients method across all layers of BERT reveals a strong upper-layer bias: [[knowledge-neurons]] cluster predominantly in the top feed-forward network (FFN) sublayers, with very few identified in lower or middle layers (arXiv:2104.08696). This distributional finding contrasts with lower-level syntactic or lexical features, which tend to be represented in earlier layers, suggesting a hierarchical organization where semantic factual associations emerge only after extensive contextual processing. The upper-layer concentration is consistent with the [[ffn-as-key-value-memory]] hypothesis, in which value retrieval happens late in the network.
