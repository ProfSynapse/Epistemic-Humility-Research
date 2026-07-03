---
aliases:
- Primitives pretraining increases abstract representation geometry
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:primitives-pretraining-increases-parallelism-score
  type: mechanism
  status: canonical
cause: "[[primitives-pretraining]] (exposure to 1-rule and 2-rule subtask variants before the full C-PRO compositional task) providing the model with decomposed rule components before joint rule application"
effect: "Higher [[parallelism-score]] of ANN hidden-layer representations on the full compositional task, indicating more abstract and parallelogram-structured internal geometry"
polarity: increases
related:
- '[[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]'
- '[[primitives-pretraining]]'
- '[[parallelism-score]]'
- '[[abstract-representations]]'
relationships:
- type: supported_by
  target: '[[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]'
  target_id: paper:2209.07431
  confidence: high
- type: related_to
  target: '[[primitives-pretraining]]'
  target_id: method:primitives-pretraining
- type: related_to
  target: '[[parallelism-score]]'
  target_id: metric:parallelism-score
- type: related_to
  target: '[[abstract-representations]]'
  target_id: term:abstract-representations
---

Exposing a network to primitive rule components (individual transformation rules) before the full compositional task biases the network toward representing those rules as separable, reusable dimensions rather than fused task-specific patterns. The compositional generalisation paper (arXiv:2209.07431) measures this structural change via the parallelism score, which quantifies how close the hidden-state geometry is to a parallelogram (the geometry expected from abstract factored representations). Networks with primitives pretraining show substantially higher parallelism scores, explaining their improved zero-shot compositional generalisation.
