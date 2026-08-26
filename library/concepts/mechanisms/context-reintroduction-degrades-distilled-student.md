---
aliases:
- Context-induced degradation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:context-reintroduction-degrades-distilled-student
  type: mechanism
  status: canonical
cause: "Training a context-free student to internalize privileged context via standard [[on-policy-distillation]] (optimizing only privileged fidelity), then reintroducing the same privileged context at inference time"
effect: "Accuracy drops relative to the context-free student, sometimes overturning predictions the student already got correct without the context, even though the context is the very information the student was trained to internalize"
polarity: decreases
related:
- '[[2606.11627--when-context-returns-toward-robust-internalization-policy]]'
- '[[on-policy-distillation]]'
- '[[context-invariance]]'
- '[[no-context-anchoring-mitigates-context-induced-degradation]]'
relationships:
- type: supported_by
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
  target: '[[no-context-anchoring-mitigates-context-induced-degradation]]'
  target_id: mechanism:no-context-anchoring-mitigates-context-induced-degradation
  confidence: high
---

Wang et al. (2026) name this counterintuitive effect "context-induced degradation": across 14 (model, task) configurations spanning System-Prompt QA, Text Games, and Mathematical Reasoning, standard OPD-trained students show non-trivial "context harm" (accuracy loss when the internalized context is put back in the prompt) in all 8 System-Prompt QA settings tested in detail. The most severe case, Llama-3.2-3B-Instruct on MedMCQA, reaches a Harm rate of 15.7%, with context-conditioned accuracy falling 9.5 points below context-free accuracy (Table 1, Section 5.2.1). Even Qwen3-8B, whose base model performs similarly under both views, still shows a non-trivial 5.5% harm rate after OPD on the Safety task, showing strong initial performance does not guarantee robustness to context reintroduction. The authors trace the cause to an asymmetry in the OPD objective: it optimizes only "privileged fidelity" (the context-free student must match the context-conditioned teacher) while leaving the student's own behavior with context present entirely unconstrained, so nothing during training prevents the student from behaving worse once that context reappears.
