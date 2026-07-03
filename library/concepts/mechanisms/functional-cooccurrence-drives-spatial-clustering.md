---
aliases:
- Functional Co-occurrence Drives Spatial Clustering of SAE Features
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:functional-cooccurrence-drives-spatial-clustering
  type: mechanism
  status: canonical
cause: "SAE features that tend to fire together within documents (functional co-occurrence, measured by [[phi-coefficient-cooccurrence]]) share semantic content"
effect: "Functionally similar SAE features cluster together spatially in the feature point cloud, forming interpretable lobes such as a math/code lobe"
polarity: enables
related:
- '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
- '[[sparse-autoencoder]]'
- '[[sae-functional-modularity]]'
- '[[phi-coefficient-cooccurrence]]'
relationships:
- type: supported_by
  target: '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
  target_id: paper:2410.19750
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[sae-functional-modularity]]'
  target_id: term:sae-functional-modularity
- type: related_to
  target: '[[phi-coefficient-cooccurrence]]'
  target_id: metric:phi-coefficient-cooccurrence
---

The phi-coefficient co-occurrence matrix of SAE features (computed over a large corpus) provides a functional similarity measure that is predictive of spatial proximity in the feature embedding space. Features that co-occur frequently occupy nearby regions of the feature cloud, and those regions correspond to coherent semantic domains (arXiv:2410.19750). This spatial clustering is a geometric fingerprint of the [[sae-functional-modularity]] property and implies that the organisation of SAE features reflects the statistical structure of the training data rather than a uniform distribution over concept space.
