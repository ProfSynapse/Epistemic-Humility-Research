---
aliases:
- cross-model layer correspondence probing
- inter-model linear layer mapping
tags:
- kg/method
- concept
- method
kg:
  id: method:cross-model-layer-correspondence-probing
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
  target_id: paper:2505.13898
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

Cross-model layer correspondence probing trains a linear map from every layer
of one model's residual stream to every layer of a second, independently
trained model's residual stream (typically a shallower and a deeper model from
the same family), then reads the resulting matrix of prediction errors as a
correspondence map between the two models' layers. A diagonal pattern of
lowest error indicates that layers at matched relative depth (fraction of
total depth) correspond best.

**Why it matters here:** [[2505.13898--do-language-models-use-their-depth-efficiently]]
applies this method between Qwen 2.5 1.5B and Qwen 2.5 14B and finds a clear
relative-depth diagonal, which it takes as evidence that the deeper model
spreads the same kind of computation over more layers rather than composing
qualitatively new computation.

**Lineage:** a comparative extension of single-model [[residual-stream]]
probing to pairs of independently trained models of different depth.
