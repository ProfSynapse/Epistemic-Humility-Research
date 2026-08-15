---
aliases:
- NCA
- No-Context Anchoring
tags:
- kg/method
- concept
- method
kg:
  id: method:no-context-anchoring
  type: method
  status: canonical
area: methods
related:
- '[[2606.11627--when-context-returns-toward-robust-internalization-policy]]'
- '[[on-policy-distillation]]'
- '[[context-invariance]]'
- '[[kl-divergence]]'
relationships:
- type: proposed_by
  target: '[[2606.11627--when-context-returns-toward-robust-internalization-policy]]'
  target_id: paper:2606.11627
  confidence: high
- type: related_to
  target: '[[on-policy-distillation]]'
  target_id: method:on-policy-distillation
  confidence: high
- type: related_to
  target: '[[context-invariance]]'
  target_id: term:context-invariance
  confidence: high
- type: related_to
  target: '[[kl-divergence]]'
  target_id: metric:kl-divergence
  confidence: high
---

A lightweight consistency regularizer added to on-policy distillation training: the student's own no-context output is treated as a stop-gradient anchor, and the student's context-conditioned output is aligned to that anchor via forward KL divergence, adding only one extra forward pass per training step. This directly penalizes the student for behaving differently when the privileged context is reintroduced, targeting [[context-invariance]] as an explicit constraint on top of the standard privileged-fidelity objective.

**Why it matters here:** NCA demonstrates a concrete fix for the divergence between prompted (context-present) and trained (context-free) behavior discovered as [[context-reintroduction-degrades-distilled-student]]; the general pattern (regularizing a trained model's behavior to be stable whether or not a would-be prompt/context is present) is a reusable idea for probing whether abstention training produces behavior that is robust to re-presenting the training-time conditioning signal, versus behavior that only holds in its absence.
