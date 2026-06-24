---
aliases:
- monitor accuracy
- monitorability score
- latent prediction accuracy
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:latent-variable-monitor-accuracy
  type: metric
  status: canonical
area: metrics
related:
- '[[2512.00218--reasoning-under-pressure-monitorability]]'
- '[[cot-monitorability]]'
- '[[auroc]]'
- '[[abstain-accuracy]]'
- '[[generation-discrimination-gap]]'
relationships:
- type: proposed_by
  target: '[[2512.00218--reasoning-under-pressure-monitorability]]'
  target_id: paper:2512.00218
  confidence: high
- type: related_to
  target: '[[cot-monitorability]]'
  target_id: term:cot-monitorability
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[abstain-accuracy]]'
  target_id: metric:abstain-accuracy
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
---

The fraction of test examples on which a monitor LLM, given only the reasoner's CoT, correctly predicts the value of a latent variable whose ground truth is known. Evaluated on a balanced test set (equal positive and negative examples) so chance is 50%; reported as an absolute accuracy and as a change in percentage points from a controlled baseline with accuracy held within 5%.

**Why it matters here:** Provides a ground-truth-calibrated measure of CoT faithfulness that does not require human annotation of reasoning quality; allows statistical significance testing (McNemar or z-test) and direct comparison across training incentive conditions while factoring out confounds from changes in reasoner accuracy.

**Lineage:** Defined in MacDermott et al. 2025 (arXiv:2512.00218) as the primary dependent variable in a study of training incentives and CoT monitorability.
