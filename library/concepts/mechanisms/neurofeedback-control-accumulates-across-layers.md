---
aliases:
- Neurofeedback control accumulates across layers
- Distributed layers build a prompted activation shift
- Target-axis control is not localized to one block
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:neurofeedback-control-accumulates-across-layers
  type: mechanism
  status: canonical
cause: "Prompt-conditioned computation recruits contributions across successive attention and MLP blocks."
effect: "Projection onto the target residual-stream direction grows before the target layer and can plateau after it."
polarity: mediates
related:
- '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
- '[[llm-neurofeedback]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
  target_id: paper:2505.13763
  confidence: medium
- type: related_to
  target: '[[llm-neurofeedback]]'
  target_id: method:llm-neurofeedback
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

Layerwise projections show target control building gradually before the layer
used to define the target direction, with some conditions plateauing afterward.
The paper therefore describes a distributed accumulation pattern rather than a
single localized controller.
