---
aliases:
- metacognitive data selection improves faithful calibration
- self-assessed examples improve calibration training
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:metacognitive-data-selection-improves-faithful-calibration
  type: mechanism
  status: canonical
cause: "Selecting training examples from both high and low ends of a model's self-assessed metacognitive alignment scores."
effect: "Better faithful-calibration training data than random or active-learning-style selection."
polarity: increases
related:
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[metacognitive-data-selection]]'
- '[[faithful-calibration]]'
- '[[cmfg-star-equal-mass]]'
relationships:
- type: supported_by
  target: '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
  target_id: paper:2606.32032
  confidence: high
  evidence:
  - "Table 3"
  - "Table 27"
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
---

The paper provides evidence that a model's own self-assessment can rank training examples in a way that improves downstream faithful calibration. Table 3/Table 27 show metacognitive selection beating random and active-learning-style selection on average `cMFG*` for both Llama3.1-8B-Instruct and Qwen3-8B.
