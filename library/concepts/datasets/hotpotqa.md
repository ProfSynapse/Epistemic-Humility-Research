---
aliases:
- HotPotQA
- HotpotQA distractor
- HotpotQA-Modified
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:hotpotqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2507.16806--rlcr-beyond-binary-rewards]]'
- '[[rlcr]]'
- '[[expected-calibration-error]]'
- '[[brier-score]]'
- '[[calibration]]'
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
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
---

A multi-hop question answering dataset requiring reasoning over multiple paragraphs. The distractor version provides 10 paragraphs per question (2 relevant, 8 distractors). RLCR uses a modified version (HotpotQA-Modified) that removes 0, 1, or both relevant paragraphs to create varying information completeness for testing uncertainty reasoning.

**Why it matters here:** Tests calibration under incomplete or distracting evidence; the modified version with removed evidence paragraphs specifically probes whether models know when they cannot answer, making it suitable for epistemic humility research.

**Lineage:** Original HotpotQA by Yang et al. 2018; the RLCR-Modified variant adds controlled information removal to create calibration-targeted evaluation conditions.
