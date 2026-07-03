---
aliases:
- ASR
- jailbreak success rate
- Attack Success Rate (ASR)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:attack-success-rate
  type: metric
  status: canonical
area: safety-alignment
related:
- '[[jailbreakbench]]'
- '[[strong-reject-score]]'
- '[[harmbench]]'
relationships:
- type: related_to
  target: '[[jailbreakbench]]'
  target_id: dataset:jailbreakbench
- type: related_to
  target: '[[strong-reject-score]]'
  target_id: metric:strong-reject-score
- type: related_to
  target: '[[harmbench]]'
  target_id: dataset:harmbench
---

Attack Success Rate (ASR) is the fraction of adversarial or
intervention-based jailbreak attempts that successfully elicit a harmful
response from a safety-aligned language model. Each attempt is judged by an
automated evaluator (commonly a fine-tuned judge such as StrongREJECT or
HarmBench's classifier) and scored as a binary success or failure; ASR is the
mean over the attempt set. Higher ASR indicates a more effective bypass of the
refusal mechanism, whether through prompt manipulation, activation editing, or
direction ablation.

**Why it matters here:** ASR is the primary downstream measure for evaluating
whether geometric interventions on refusal directions (ablation, cone
projection) degrade the model's safety posture, and it therefore bounds how
aggressively epistemic-humility interventions can reshape caution-adjacent
directions without unacceptable safety cost.

**Lineage:** benchmark ecosystem: [[jailbreakbench]] and [[harmbench]] provide
standardised attack sets; [[strong-reject-score]] is one widely adopted
automated judge used to compute per-attempt scores.
