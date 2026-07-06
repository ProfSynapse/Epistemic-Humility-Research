---
aliases:
- RLMF
- reinforcement learning with metacognitive feedback
- metacognitive advantage scaling
tags:
- kg/method
- concept
- method
kg:
  id: method:reinforcement-learning-with-metacognitive-feedback
  type: method
  status: canonical
area: methods
related:
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[group-relative-policy-optimization]]'
- '[[metacognitive-data-selection]]'
- '[[faithful-calibration]]'
- '[[cmfg-star-equal-mass]]'
- '[[consistency-based-confidence]]'
- '[[metacognitive-advantage-scaling-improves-faithful-calibration]]'
relationships:
- type: proposed_by
  target: '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
  target_id: paper:2606.32032
  confidence: high
- type: derived_from
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[metacognitive-data-selection]]'
  target_id: method:metacognitive-data-selection
  confidence: high
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: high
- type: related_to
  target: '[[cmfg-star-equal-mass]]'
  target_id: metric:cmfg-star-equal-mass
  confidence: high
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: high
- type: related_to
  target: '[[metacognitive-advantage-scaling-improves-faithful-calibration]]'
  target_id: mechanism:metacognitive-advantage-scaling-improves-faithful-calibration
  confidence: high
---

Reinforcement learning with metacognitive feedback is a post-training method that modifies GRPO-style advantage scores using a model's self-judged performance accuracy. In the faithful-calibration setting, it gives extra weight to completions that are both above average on the primary faithfulness reward and accurate in judging their own faithful-calibration level.

**Why it matters here:** RLMF is a concrete training objective for making uncertainty expression track internal confidence rather than merely rewarding confident or cautious surface forms.

**Lineage:** Derived from [[group-relative-policy-optimization]] and internal-feedback RL, but shifts the internal signal from confidence itself to the quality of the model's self-assessment.
