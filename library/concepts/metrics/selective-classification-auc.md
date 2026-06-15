---
aliases:
- AUC
- selective accuracy-coverage AUC
- area under selective accuracy curve
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:selective-classification-auc
  type: metric
  status: canonical
area: metrics
related:
- '[[auroc]]'
- '[[expected-calibration-error]]'
relationships:
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
---

Selective-classification AUC is the area under the curve traced by plotting
selective accuracy against coverage as a confidence threshold is swept from high
to low. At any threshold the model answers only questions whose confidence
exceeds it (coverage) and is evaluated only on those answers (selective
accuracy). A model with well-ranked confidence scores will maintain high
accuracy at low coverage and degrade gracefully as coverage rises, yielding a
larger AUC.

**Why it matters here:** In the SFT-vs-DPO-vs-KTO abstention study, this metric
captures whether the model's confidence scores are diagnostic of correctness,
not just whether the model abstains at the right rate. A method that abstains on
the wrong questions can have good [[abstention-rate]] but poor
selective-classification AUC.

**Lineage:** related to [[auroc]] (ranks by confidence rather than a binary
classifier score) and [[expected-calibration-error]] (both capture confidence
reliability, from complementary angles).
