---
aliases:
- MedQA
- medical QA
- medical question answering
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:medqa
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

MedQA is a medical question-answering benchmark commonly used to evaluate clinical-domain factual and reasoning ability. In the Rewarding Doubt paper it is used as an out-of-domain transfer target for confidence-calibrated answer generation.

**Why it matters here:** Medical QA makes miscalibrated confidence especially consequential, so it is a useful stress case for epistemic humility methods that aim to preserve utility while reducing confident error.
