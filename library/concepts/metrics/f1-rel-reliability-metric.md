---
aliases:
- F1_rel
- reliability F1
- harmonic reliability metric
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:f1-rel-reliability-metric
  type: metric
  status: canonical
area: metrics
related:
- '[[2510.24020--fiscore-semantic-confidence-reward]]'
- '[[self-knowledge-f1]]'
- '[[effective-reliability]]'
- '[[llm-reliability-score]]'
- '[[abstention-rate]]'
- '[[abstention-recall]]'
- '[[over-abstention]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2510.24020--fiscore-semantic-confidence-reward]]'
  target_id: paper:2510.24020
  confidence: high
- type: related_to
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
  confidence: medium
- type: related_to
  target: '[[effective-reliability]]'
  target_id: metric:effective-reliability
  confidence: medium
- type: related_to
  target: '[[llm-reliability-score]]'
  target_id: metric:llm-reliability-score
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
- type: related_to
  target: '[[abstention-recall]]'
  target_id: metric:abstention-recall
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

The harmonic mean of F1_ans (helpfulness F1 on Known questions, which penalizes incorrect answers and over-abstentions) and F1_abs (truthfulness F1 on Unknown questions, which penalizes failures to abstain). Both components are derived from a 2x3 abstention confusion matrix partitioned by pre-fine-tuning model correctness (Known/Unknown) and refined-model outcome (correctly answered, incorrectly answered, abstained). In the ideal case F1_rel = 1; in the worst case F1_rel = 0.

**Why it matters here:** Provides a single composite score that balances helpfulness and truthfulness without requiring a calibration probe or thresholding heuristic, and that is monotonically sensitive to all four error categories simultaneously. Contrasts with the Reliability Score (RS) proposed by Xu et al. 2024, which the paper demonstrates inadvertently encourages hallucination.

**Lineage:** Proposed in this paper (An and Xu 2025, arXiv:2510.24020) as the primary evaluation metric for FiSCoRe and all baselines. Operationalizes the 2x3 abstention confusion matrix introduced in §2.1.
