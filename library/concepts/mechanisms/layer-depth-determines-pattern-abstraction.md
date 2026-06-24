---
aliases:
- Layer Depth Determines Pattern Abstraction Level
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:layer-depth-determines-pattern-abstraction
  type: mechanism
  status: canonical
cause: Depth of a feed-forward layer in the [[transformer-feed-forward-layer]] stack
effect: Type of input pattern captured by memory keys -- shallow n-gram patterns in lower layers, semantic and topic patterns in upper layers
polarity: enables
related:
- '[[2012.14913--transformer-ff-layers-key-value-memories]]'
- '[[transformer-feed-forward-layer]]'
- '[[layer-depth-pattern-hierarchy]]'
relationships:
- type: supported_by
  target: '[[2012.14913--transformer-ff-layers-key-value-memories]]'
  target_id: paper:2012.14913
  confidence: high
- type: related_to
  target: '[[transformer-feed-forward-layer]]'
  target_id: term:transformer-feed-forward-layer
- type: related_to
  target: '[[layer-depth-pattern-hierarchy]]'
  target_id: term:layer-depth-pattern-hierarchy
---

Feed-forward layers in transformers act as key-value memories, with keys matching input patterns and values producing output distributions. Lower-layer keys respond to surface n-gram co-occurrences, while upper-layer keys respond to semantic or topic-level abstractions, as demonstrated by the pattern-retrieval experiments in Geva et al. (arXiv:2012.14913). This depth-abstraction gradient means the network's knowledge is hierarchically organized rather than uniformly distributed.
