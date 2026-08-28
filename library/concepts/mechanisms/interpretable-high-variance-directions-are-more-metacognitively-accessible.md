---
aliases:
- Interpretable high-variance directions are easier to report and control
- Semantic meaning and explained variance predict neurofeedback access
- Metacognitive access favors interpretable activation axes
- Which latent directions can a model report about itself
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:interpretable-high-variance-directions-are-more-metacognitively-accessible
  type: mechanism
  status: canonical
cause: "An activation direction has clear semantic meaning, explains more residual-stream variance, or both."
effect: "A model more accurately reports its discretized activation label and more strongly shifts activation toward a prompted target label."
polarity: enables
related:
- '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
- '[[llm-neurofeedback]]'
- '[[metacognitive-space]]'
relationships:
- type: supported_by
  target: '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
  target_id: paper:2505.13763
  confidence: high
- type: related_to
  target: '[[llm-neurofeedback]]'
  target_id: method:llm-neurofeedback
  confidence: high
- type: related_to
  target: '[[metacognitive-space]]'
  target_id: term:metacognitive-space
  confidence: high
---

Logistic-regression directions were reported and controlled more successfully
than principal components, while earlier high-variance principal components
outperformed later components. Performance also improved with more in-context
examples. The accessible directions formed a much smaller subspace than the
full residual stream.
