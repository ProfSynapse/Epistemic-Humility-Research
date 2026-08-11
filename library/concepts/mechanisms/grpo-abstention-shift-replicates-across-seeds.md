---
aliases:
- GRPO abstention shift replicates across seeds
- G1 (grpo-three-seed-confirmatory)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:grpo-abstention-shift-replicates-across-seeds
  type: mechanism
  status: canonical
cause: "GRPO fine-tuning of the clean response-confidence SFT lineage (clean_sft_grpo_v2), evaluated against its own same-seed pre-GRPO base on the full 3369-row SelfAware set"
effect: "answer-on-unknown decreases and refusal recall increases by more than the pre-registered 3.0 pp floor in both of two fresh training seeds, replicating the seed-1 direction and a comparable magnitude, at the cost of a larger rise in over-refusal and an essentially flat truthful rate"
polarity: enables
related:
- '[[grpo-three-seed-confirmatory]]'
- '[[grpo-centered-stacking]]'
relationships:
- type: supported_by
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/gates.yaml g1_grpo_abstention_shift_replicates (the falsifier gate, PASS both seeds)"
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md G1 ADJUDICATED PASS entry (seed 2 answer_on_unknown -4.36 pp / refusal_recall +4.36 pp; seed 3 -6.78 pp / +6.78 pp, both against a 3.0 pp floor)"
- type: related_to
  target: '[[grpo-centered-stacking]]'
  target_id: experiment:grpo-centered-stacking
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Effect 1 (the seed-1 GRPO abstention shift this mechanism replicates: 12.98 to 6.59 pp answer-on-unknown, 87.02 to 93.41 pp refusal recall)"
---

Registered as the falsifier gate of `grpo-three-seed-confirmatory` (G1):
answer-on-unknown and refusal recall are exact complements on the
1032 unknown-labeled SelfAware rows, so the two conditions are one
measurement, not two corroborating findings. The shift held in both fresh
seeds (seed 2: -4.36 pp / +4.36 pp; seed 3: -6.78 pp / +6.78 pp), clearing
the floor with margin in both. The pass has a documented cost: over-refusal
rose more than the abstention gain in both seeds (+8.51 pp, +9.67 pp) and
`truthful_pct` moved only +0.18 pp / +0.53 pp, arithmetically forced by a
refusal-recall gain nearly cancelling a correct-known-answer headcount loss.
On this instrument the shift reads as a redistribution of the refuse/answer
tradeoff rather than a net truthfulness gain.
