---
aliases:
- Higher parallelism score enables zero-shot generalization
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:abstract-representations-enable-zero-shot-generalization
  type: mechanism
  status: canonical
cause: "High degree of abstract (parallel) representation in ANN hidden layers, as measured by [[parallelism-score]], indicating that compositional rule dimensions are encoded orthogonally and reusably"
effect: "Higher zero-shot accuracy on held-out C-PRO task combinations not seen during training, demonstrating [[zero-shot-compositional-generalization]]"
polarity: increases
related:
- '[[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]'
- '[[abstract-representations]]'
- '[[parallelism-score]]'
- '[[zero-shot-compositional-generalization]]'
relationships:
- type: supported_by
  target: '[[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]'
  target_id: paper:2209.07431
  confidence: high
- type: related_to
  target: '[[abstract-representations]]'
  target_id: term:abstract-representations
- type: related_to
  target: '[[parallelism-score]]'
  target_id: metric:parallelism-score
- type: related_to
  target: '[[zero-shot-compositional-generalization]]'
  target_id: metric:zero-shot-compositional-generalization
---

The parallelism score measures how much the hidden-state geometry resembles a parallelogram, which is the expected shape when two independent rule dimensions are encoded in orthogonal directions. Networks with high parallelism scores can recombine known rule dimensions in novel ways without additional training, because the rule dimensions function as independent basis vectors in the representation space. The compositional generalisation paper (arXiv:2209.07431) confirms this via a strong positive correlation between parallelism score measured on training combinations and zero-shot accuracy on held-out combinations, establishing abstract representation geometry as a mechanistic predictor of generalisation.
