---
aliases:
- DPO Concentrates Persona Suppression
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-concentrates-persona-suppression
  type: mechanism
  status: canonical
cause: "[[direct-preference-optimization]] (DPO) alignment stage with preference signals against harmful content, applied after SFT and before RLVR"
effect: "Significant reduction in evil and sycophantic [[persona-vectors|persona]] steering effectiveness; SFT and RLVR stages contribute little suppression of these persona directions"
polarity: decreases
related:
- '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
- '[[persona-vectors]]'
- '[[direct-preference-optimization]]'
- '[[pretraining-checkpoint-tracing]]'
relationships:
- type: supported_by
  target: '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
  target_id: paper:2605.13329
  confidence: high
- type: related_to
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
- type: related_to
  target: '[[pretraining-checkpoint-tracing]]'
  target_id: method:pretraining-checkpoint-tracing
---

Among the alignment stages (SFT, DPO, RLVR), the DPO stage is responsible for nearly all reduction in the effectiveness of steering along evil and sycophantic persona directions. Tracing persona vector steerability across checkpoints shows that SFT and RLVR stages barely change persona steering effectiveness, while DPO substantially reduces the cosine-similarity response of model behaviour to persona vector injection (arXiv:2605.13329). This concentration of suppression in the DPO stage implies that preference-based training is uniquely positioned to modulate persona-direction representations, whereas instruction-following and reward-maximisation fine-tuning leave persona geometry largely intact.
