---
aliases:
- ΔFF
- delta-FF
- FlipFlop effect
- accuracy deterioration under challenge
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:flipflop-effect
  type: metric
  status: canonical
area: metrics
related:
- '[[2311.08596--flipflop-experiment]]'
- '[[flipflop-experiment]]'
- '[[sycophancy]]'
- '[[distractor-prompting-reveals-calibration-gap]]'
relationships:
- type: proposed_by
  target: '[[2311.08596--flipflop-experiment]]'
  target_id: paper:2311.08596
  confidence: high
- type: related_to
  target: '[[flipflop-experiment]]'
  target_id: method:flipflop-experiment
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[distractor-prompting-reveals-calibration-gap]]'
  target_id: mechanism:distractor-prompting-reveals-calibration-gap
  confidence: medium
---

The difference between a model's final prediction accuracy and its initial prediction accuracy in a two-turn FlipFlop conversation: ΔFF = Acc_final - Acc_init. A negative value indicates accuracy deterioration caused by sycophantic answer revision under challenge. Reported at the model, challenger, and task level.

**Why it matters here:** Quantifies the cost of sycophantic behavior in accuracy terms, enabling direct comparisons across models and conditions and establishing a performance target for fine-tuning or alignment interventions intended to improve robustness to social pressure.

**Lineage:** Defined in Laban et al. 2023 (arXiv 2311.08596), §3.3.
