---
aliases:
- Upper-Layer Value Vectors Predict Next-Token Distribution
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:upper-layer-values-predict-next-token
  type: mechanism
  status: canonical
cause: Position of a feed-forward layer in the upper portion of the [[transformer-feed-forward-layer]] stack
effect: Value vectors induce output vocabulary distributions correlated with the next-token prediction for their key trigger patterns, with agreement rates rising to ~3.5% in top layers versus a 0.0004% random baseline
polarity: increases
related:
- '[[2012.14913--transformer-ff-layers-key-value-memories]]'
- '[[transformer-feed-forward-layer]]'
relationships:
- type: supported_by
  target: '[[2012.14913--transformer-ff-layers-key-value-memories]]'
  target_id: paper:2012.14913
  confidence: high
- type: related_to
  target: '[[transformer-feed-forward-layer]]'
  target_id: term:transformer-feed-forward-layer
---

In transformer feed-forward layers analyzed by Geva et al. (arXiv:2012.14913), value vectors serve as output distributions over the vocabulary, and upper-layer values are systematically aligned with the next-token predictions for the patterns their keys detect. The agreement rate between a value vector's top vocabulary prediction and the model's final prediction climbs to roughly 3.5% in the uppermost layers -- thousands of times higher than chance. This supports the interpretation that upper-layer values directly encode next-token knowledge rather than intermediate representations.
