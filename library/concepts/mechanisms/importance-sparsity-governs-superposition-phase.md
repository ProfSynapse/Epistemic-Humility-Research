---
aliases:
- Importance and Sparsity Jointly Govern Superposition Phase
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:importance-sparsity-governs-superposition-phase
  type: mechanism
  status: canonical
cause: Interaction of relative feature importance and feature sparsity in a neural network's training objective
effect: Discontinuous first-order phase transitions determine whether a feature is not learned, learned in superposition, or assigned a dedicated dimension, producing the superposition phase diagram
polarity: enables
related:
- '[[tc2022--toy-models-of-superposition]]'
- '[[superposition-hypothesis]]'
- '[[superposition-phase-diagram]]'
- '[[superposition-geometry]]'
relationships:
- type: supported_by
  target: '[[tc2022--toy-models-of-superposition]]'
  target_id: paper:tc2022
  confidence: high
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: related_to
  target: '[[superposition-phase-diagram]]'
  target_id: method:superposition-phase-diagram
---

Elhage et al. (tc2022) derive a phase diagram showing that the network's decision to represent a feature in superposition or with a dedicated dimension is governed jointly by that feature's relative importance and its sparsity. As either quantity crosses critical thresholds, the network undergoes a sudden, discontinuous (first-order) transition between representational regimes. This explains why features are not uniformly stored and why small changes in data distribution or model capacity can cause abrupt qualitative shifts in internal representations.
