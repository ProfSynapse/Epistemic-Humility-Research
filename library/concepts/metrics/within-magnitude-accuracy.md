---
aliases:
- WMA
- within one order of magnitude accuracy
- Within-Magnitude Accuracy
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:within-magnitude-accuracy
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
- '[[lre-based-frequency-estimation]]'
- '[[subject-object-co-occurrence-frequency]]'
relationships:
- type: proposed_by
  target: '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
  target_id: paper:2504.12459
  confidence: high
- type: related_to
  target: '[[lre-based-frequency-estimation]]'
  target_id: method:lre-based-frequency-estimation
---

Within-magnitude accuracy (WMA) is the proportion of frequency predictions from a regression model that fall within one order of magnitude of the ground-truth pretraining co-occurrence count. It is the primary evaluation metric for [[lre-based-frequency-estimation]] because exact count prediction is intractable: ground-truth counts span many orders of magnitude and the regression task is inherently noisy. A prediction is scored correct if it satisfies |log10(predicted / ground_truth)| at most 1.

**Why it matters here:** WMA determines whether frequency estimation is actionable for auditing knowledge boundaries: a regressor with high WMA can provide rough but informative estimates of what a closed LM has memorized, supporting external calibration diagnostics relevant to epistemic humility.

**Lineage:** defined in [[2504.12459--linear-representations-pretraining-data-frequency-language-models]] as the evaluation standard for the [[lre-based-frequency-estimation]] regression task over [[subject-object-co-occurrence-frequency]] counts.
