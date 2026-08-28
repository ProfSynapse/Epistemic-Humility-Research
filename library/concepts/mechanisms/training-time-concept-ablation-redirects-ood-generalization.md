---
aliases:
- Training-time concept ablation redirects out-of-distribution generalization
- Latent ablation during fine-tuning changes learned generalization
- Ablating a concept only during training changes later behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:training-time-concept-ablation-redirects-ood-generalization
  type: mechanism
  status: canonical
cause: "[[concept-ablation-finetuning]] removes selected undesired latent directions during each training forward pass."
effect: "Weight updates learn alternative predictors, reducing the associated out-of-distribution behavior after the ablation is removed."
polarity: explains
related:
- '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
- '[[concept-ablation-finetuning]]'
- '[[emergent-misalignment]]'
relationships:
- type: supported_by
  target: '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
  target_id: paper:2507.16795
  confidence: high
- type: related_to
  target: '[[concept-ablation-finetuning]]'
  target_id: method:concept-ablation-finetuning
  confidence: high
- type: related_to
  target: '[[emergent-misalignment]]'
  target_id: term:emergent-misalignment
  confidence: high
---

Concept Ablation Fine-Tuning applies the projection only while weights are
being updated. The trained model then runs without an activation intervention.
Across emergent-misalignment and synthetic spurious-correlation tasks, selected
concept ablations changed later out-of-distribution behavior more reliably than
matched random or uninterpreted direction controls.

**Scope:** The evidence concerns fixed, selected concept subspaces. It does not
show that a model can dynamically consult an internal answerability signal.
