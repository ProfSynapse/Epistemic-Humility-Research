---
aliases:
- miscalibration
- confidence overestimation
tags:
- kg/term
- concept
- term
kg:
  id: term:overconfidence
  type: term
  status: canonical
area: terms
related:
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[verbalized-confidence]]'
relationships:
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
---

Overconfidence is a calibration failure in which a model's expressed confidence is systematically higher than its actual accuracy. In a well-calibrated system, responses given 80% confidence should be correct 80% of the time; an overconfident model instead achieves substantially lower accuracy than its stated confidence implies, across the full range of confidence buckets. The failure is especially consequential in high-stakes domains where users rely on the model's stated certainty to decide how much to trust an answer.

**Why it matters here:** Overconfidence is the primary failure mode that abstention training aims to correct: an overconfident model never abstains when it should, so measuring and reducing it is central to the SFT-vs-DPO-vs-KTO abstention comparison.

**Lineage:** related to [[calibration]], [[expected-calibration-error]], and [[verbalized-confidence]].
