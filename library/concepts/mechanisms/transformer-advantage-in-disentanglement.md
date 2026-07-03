---
aliases:
- Transformers disentangle representations more efficiently than RNNs
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:transformer-advantage-in-disentanglement
  type: mechanism
  status: canonical
cause: "Transformer (GPT-2) architecture processing multi-task [[evidence-accumulation-task|evidence accumulation]], whose attention mechanism can selectively route task-relevant evidence to independent output heads"
effect: "Near-perfect [[ood-coefficient-of-determination|OOD R^2]] already at N_task = D, whereas RNNs require substantially larger N_task or exhibit more gradual phase transitions, especially at higher latent dimensionality D"
polarity: increases
related:
- '[[2407.11249--disentangling-representations-through-multi-task-learning]]'
- '[[disentangled-representation]]'
- '[[ood-coefficient-of-determination]]'
- '[[multi-task-learning]]'
relationships:
- type: supported_by
  target: '[[2407.11249--disentangling-representations-through-multi-task-learning]]'
  target_id: paper:2407.11249
  confidence: high
- type: related_to
  target: '[[disentangled-representation]]'
  target_id: term:disentangled-representation
- type: related_to
  target: '[[ood-coefficient-of-determination]]'
  target_id: metric:ood-coefficient-of-determination
- type: related_to
  target: '[[multi-task-learning]]'
  target_id: method:multi-task-learning
---

Transformers can in principle assign each attention head to a different task-specific boundary, implementing perfect task routing without shared computation, whereas RNNs must process all tasks through a shared hidden-state bottleneck. This architectural difference manifests as a steeper and earlier phase transition to disentangled representations in transformers: GPT-2 achieves near-perfect OOD R^2 as soon as N_task reaches D, while RNNs require N_task to substantially exceed D, particularly when the latent space is higher-dimensional (arXiv:2407.11249). The transformer's modular attention structure is therefore an inductive bias that favours disentanglement in multi-task settings.
