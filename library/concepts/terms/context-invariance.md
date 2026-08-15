---
aliases:
- Context invariance
- Robust internalization
tags:
- kg/term
- concept
- term
kg:
  id: term:context-invariance
  type: term
  status: canonical
area: terms
related:
- '[[2606.11627--when-context-returns-toward-robust-internalization-policy]]'
- '[[on-policy-distillation]]'
- '[[context-reintroduction-degrades-distilled-student]]'
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
  target: '[[context-reintroduction-degrades-distilled-student]]'
  target_id: mechanism:context-reintroduction-degrades-distilled-student
  confidence: high
---

Wang et al. (2026) define context invariance as the property that, once privileged context has been internalized into a model's parameters via distillation, the model's output should remain stable regardless of whether that same context is present or absent at inference time. It is proposed as a complement to the standard on-policy-distillation objective ("privileged fidelity," which only requires the context-free student to match the context-conditioned teacher), because privileged fidelity alone does not constrain, and in practice does not guarantee, stability under context reintroduction.

**Why it matters here:** context invariance names the property that fails in [[context-reintroduction-degrades-distilled-student]] (context-induced degradation) and is the target property [[no-context-anchoring]] is designed to promote; it generalizes the earlier weights-vs-prompt equivalence question (Askell et al.'s [[context-distillation]]) to a two-sided question of whether internalized behavior is robust to the original signal being put back.
