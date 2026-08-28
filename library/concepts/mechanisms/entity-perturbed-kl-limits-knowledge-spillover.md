---
aliases:
- Entity-perturbed KL limits knowledge spillover
- Teacher matching on fictitious neighboring entities preserves abstention
- Local output regularization sharpens knowledge boundaries
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:entity-perturbed-kl-limits-knowledge-spillover
  type: mechanism
  status: canonical
cause: "During knowledge fine-tuning, a KL penalty matches the frozen base model on inputs whose subject entity is replaced by a fictitious alternative."
effect: "The learned target fact is less likely to spill over to nearby unseen entities, preserving their prior abstention behavior."
polarity: prevents
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[sparse-entity-aware-tuning]]'
- '[[kl-divergence-penalty]]'
- '[[self-distillation-suppresses-representational-drift]]'
relationships:
- type: supported_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: related_to
  target: '[[sparse-entity-aware-tuning]]'
  target_id: method:sparse-entity-aware-tuning
  confidence: high
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: high
- type: related_to
  target: '[[self-distillation-suppresses-representational-drift]]'
  target_id: mechanism:self-distillation-suppresses-representational-drift
  confidence: medium
---

Adding entity perturbation to sparse fine-tuning increased human-judged
abstention from 0.806 to 0.954 in the reported PISTOL ablation. The improvement
persisted across random, magnitude-based, and importance-based parameter masks,
supporting a local knowledge-spillover effect beyond global sparsity.
