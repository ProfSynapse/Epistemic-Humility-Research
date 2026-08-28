---
aliases:
- Sparse Entity-Aware Tuning
- SEAT
- Sparse entity-aware knowledge adaptation
tags:
- kg/method
- concept
- method
kg:
  id: method:sparse-entity-aware-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[supervised-finetuning]]'
- '[[kl-divergence-penalty]]'
relationships:
- type: proposed_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: derived_from
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: high
---

Sparse Entity-Aware Tuning combines masked parameter updates with an
entity-perturbed KL penalty. It randomly replaces each training subject with a
fictitious entity, then constrains the adapted model to match the frozen base
model's output distribution on that neighboring input.

**Why it matters here:** SEAT preserves an existing output-level abstention
policy during knowledge adaptation without using abstention examples in its
training objective. It does not read an answerability scalar or gate generation
from hidden states.

**Lineage:** It adds sparse coordinate updates and local teacher-distribution
regularization to [[supervised-finetuning]].
