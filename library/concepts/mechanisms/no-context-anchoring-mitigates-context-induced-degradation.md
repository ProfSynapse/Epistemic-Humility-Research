---
aliases:
- NCA reduces context harm
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:no-context-anchoring-mitigates-context-induced-degradation
  type: mechanism
  status: canonical
cause: "Adding [[no-context-anchoring]] (a forward-KL consistency penalty between the student's context-conditioned output and its own stop-gradient no-context output) to standard on-policy distillation training"
effect: "Context harm drops and both-view (context-free and context-conditioned) accuracy improves in the large majority of tested configurations, without sacrificing no-context performance"
polarity: decreases
related:
- '[[2606.11627--when-context-returns-toward-robust-internalization-policy]]'
- '[[no-context-anchoring]]'
- '[[context-reintroduction-degrades-distilled-student]]'
relationships:
- type: supported_by
  target: '[[2606.11627--when-context-returns-toward-robust-internalization-policy]]'
  target_id: paper:2606.11627
  confidence: high
- type: related_to
  target: '[[no-context-anchoring]]'
  target_id: method:no-context-anchoring
  confidence: high
- type: related_to
  target: '[[context-reintroduction-degrades-distilled-student]]'
  target_id: mechanism:context-reintroduction-degrades-distilled-student
  confidence: high
---

Across 14 configurations, NCA improves context-conditioned accuracy in the majority of settings and reduces context harm in 12 of 14, for an average 7.2-percentage-point reduction in harm and a 5.3-point gain in both-view success (Figure 1 middle, Section 1). On the System-Prompt QA benchmarks in detail (Table 1), NCA reduces Harm and improves BothCorrect accuracy in all 8 settings, and also improves context-free accuracy in 7 of 8. The most pronounced single-setting improvement is Llama-3.2-3B-Instruct on MedMCQA, where NCA cuts Harm from 15.7% to 1.6% (a 14.1-percentage-point reduction) and raises BothCorrect from 63.1% to 73.5% (a 10.4-point gain). The one notable trade-off occurs on Qwen2.5-7B-Instruct MedMCQA, a setting where context remains genuinely beneficial to the teacher (the paper's "Regime B").
