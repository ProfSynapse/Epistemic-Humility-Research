---
aliases:
- CommonsenseQA
- Commonsense QA
- CSQA
- CsQA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:commonsenseqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]'
- '[[calibration]]'
relationships:
- type: related_to
  target: '[[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]'
  target_id: paper:2503.02623
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
---

CommonsenseQA is a multiple-choice question-answering benchmark designed to test commonsense reasoning over everyday concepts. In the Rewarding Doubt paper it is used as an out-of-domain transfer target after confidence training on TriviaQA.

**Why it matters here:** The benchmark provides a check on whether confidence-calibration training remains useful beyond the factoid distribution it was trained on.
