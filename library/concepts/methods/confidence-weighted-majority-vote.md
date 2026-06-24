---
aliases:
- confidence weighted majority vote
- confidence-weighted voting
tags:
- kg/method
- concept
- method
kg:
  id: method:confidence-weighted-majority-vote
  type: method
  status: canonical
area: methods
related:
- '[[2507.16806--rlcr-beyond-binary-rewards]]'
- '[[rlcr]]'
- '[[verbalized-confidence]]'
- '[[self-consistency]]'
- '[[brier-score]]'
relationships:
- type: proposed_by
  target: '[[2507.16806--rlcr-beyond-binary-rewards]]'
  target_id: paper:2507.16806
  confidence: high
- type: related_to
  target: '[[rlcr]]'
  target_id: method:rlcr
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: medium
---

A test-time aggregation method that weights each candidate answer's vote by the model's verbalized confidence score q, then selects the answer with the highest weighted vote total. The confidence analogue of likelihood-weighted majority vote, but using the model's own verbalized confidence rather than token probabilities.

**Why it matters here:** Enables well-calibrated verbalized confidence to improve test-time accuracy without any external reward model or additional supervision, outperforming vanilla majority vote and max-confidence selection when the model is well-calibrated.

**Lineage:** Builds on majority vote and best-of-N paradigms; requires a model trained to produce calibrated verbalized confidence (e.g., via RLCR); confidence serves as proxy reward rather than a learned reward model.
