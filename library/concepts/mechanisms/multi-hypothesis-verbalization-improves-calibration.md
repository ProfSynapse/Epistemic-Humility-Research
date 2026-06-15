---
aliases:
- Generating multiple hypotheses before committing improves verbalized calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:multi-hypothesis-verbalization-improves-calibration
  type: mechanism
  status: canonical
cause: Prompting the model to produce k candidate answers and associated probabilities (top-k verbalization) rather than a single answer
effect: '[[calibration]] of the best-ranked prediction improves over single-answer [[verbalized-confidence]]'
polarity: decreases
related:
- '[[2305.14975--just-ask-for-calibration]]'
- '[[calibration]]'
- '[[verbalized-confidence]]'
relationships:
- type: supported_by
  target: '[[2305.14975--just-ask-for-calibration]]'
  target_id: paper:2305.14975
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
---

Generating multiple hypotheses before selecting one forces the model to consider the probability mass across alternative answers, which yields a more accurate estimate of confidence in the chosen answer. Single-answer verbalization anchors on whichever answer the model generates first, which can be overconfident. The just-ask-for-calibration paper (arXiv:2305.14975) shows top-k verbalization improves [[expected-calibration-error]] over single-answer verbalization on [[triviaqa]] and [[sciq]].
