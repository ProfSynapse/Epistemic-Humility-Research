---
aliases:
- MDS
- metacognitive data selection
- self-assessment data selection
tags:
- kg/method
- concept
- method
kg:
  id: method:metacognitive-data-selection
  type: method
  status: canonical
area: methods
related:
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[reinforcement-learning-with-metacognitive-feedback]]'
- '[[faithful-calibration]]'
- '[[metacognitive-data-selection-improves-faithful-calibration]]'
relationships:
- type: proposed_by
  target: '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
  target_id: paper:2606.32032
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-with-metacognitive-feedback]]'
  target_id: method:reinforcement-learning-with-metacognitive-feedback
  confidence: high
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: high
- type: related_to
  target: '[[metacognitive-data-selection-improves-faithful-calibration]]'
  target_id: mechanism:metacognitive-data-selection-improves-faithful-calibration
  confidence: high
---

Metacognitive data selection chooses training examples using the model's own judgment of how well its expressed and internal confidence align. The paper instantiates this by scoring examples from 0 to 100 and selecting both the highest- and lowest-scoring halves of the target training budget.

**Why it matters here:** The method treats self-assessment as a data-curation signal, not only as an evaluation target, and empirically outperforms random and active-learning-style selection for faithful calibration.

**Lineage:** Related to active learning, but the acquisition signal is the model's self-rated metacognitive alignment rather than ground-truth difficulty or uncertainty alone.
