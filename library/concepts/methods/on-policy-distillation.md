---
aliases:
- OPD
- On-policy context distillation
tags:
- kg/method
- concept
- method
kg:
  id: method:on-policy-distillation
  type: method
  status: canonical
area: methods
related:
- '[[2606.11627--when-context-returns-toward-robust-internalization-policy]]'
- '[[context-distillation]]'
relationships:
- type: related_to
  target: '[[context-distillation]]'
  target_id: method:context-distillation
  confidence: high
---

On-policy distillation (OPD) trains a context-free student to internalize privileged context (a system prompt, chain-of-thought hints, or a game-state scaffold) by matching the context-conditioned output of a teacher, generalizing context distillation to allow distinct teacher and student models. The training objective, "privileged fidelity," requires only that the context-free student match the context-conditioned teacher; it leaves the student's own behavior when the context is reintroduced unconstrained.

**Why it matters here:** OPD is the modern, teacher/student generalization of the [[context-distillation]] idea from Askell et al. (2021), which used a single model as both teacher and student. Wang et al. (arXiv:2606.11627) show its privileged-fidelity-only objective has an asymmetry that causes [[context-reintroduction-degrades-distilled-student]], motivating [[no-context-anchoring]] as a fix.
