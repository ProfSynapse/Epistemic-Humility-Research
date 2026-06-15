---
aliases:
- Multi-Sample Brainstorming Improves P(True)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:multi-sample-brainstorming-improves-self-evaluation
  type: mechanism
  status: canonical
cause: Showing a language model multiple of its own temperature-1 samples before asking it to judge whether one specific answer is True or False
effect: Significant improvement in [[p-true]] [[brier-score]] on short-answer tasks; the gap between base accuracy and conditional accuracy grows with model size
polarity: decreases
related:
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[p-true]]'
- '[[brier-score]]'
relationships:
- type: supported_by
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
---

Seeing multiple of its own candidate answers gives the model implicit information about the diversity and consistency of its beliefs about a question, which it can use to calibrate its True/False judgment. When many samples agree on an answer, the model can infer higher confidence; when they disagree, it can infer lower confidence. The paper (arXiv:2207.05221) shows this brainstorming procedure substantially improves [[p-true]] Brier scores and that the benefit scales with model size.
