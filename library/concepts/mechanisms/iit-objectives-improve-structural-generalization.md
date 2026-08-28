---
aliases:
- IIT objectives improve structural and behavioral generalization
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:iit-objectives-improve-structural-generalization
  type: mechanism
  status: canonical
cause: "A neural model is trained on counterfactual labels produced by aligned interventions in a high-level causal model."
effect: "The model more closely realizes the target causal structure and generalizes better on the studied tasks."
polarity: increases
related:
- '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
- '[[interchange-intervention-training]]'
- '[[interchange-intervention-accuracy]]'
relationships:
- type: supported_by
  target: '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
  target_id: paper:2112.00826
  confidence: high
- type: related_to
  target: '[[interchange-intervention-training]]'
  target_id: method:interchange-intervention-training
  confidence: high
- type: related_to
  target: '[[interchange-intervention-accuracy]]'
  target_id: metric:interchange-intervention-accuracy
  confidence: high
---

Across MNIST-PVR, ReaSCAN, and MQNLI, IIT-trained models showed higher task performance and higher agreement with the target causal model. The evidence is task-specific and depends on preselected alignments.
