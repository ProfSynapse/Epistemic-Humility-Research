---
aliases:
- F1_rel
- reliability F1
- abstention reliability harmonic mean
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:reliability-f1
  type: metric
  status: canonical
area: metrics
related:
- '[[2604.14324--purging-gray-zone-latent-geometric-denoising-precise]]'
- '[[abstention-rate]]'
relationships:
- type: proposed_by
  target: '[[2604.14324--purging-gray-zone-latent-geometric-denoising-precise]]'
  target_id: paper:2604.14324
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: high
---

Reliability F1 is the harmonic mean of answerability F1 and abstention F1. The first component combines precision and recall for correctly answering known questions, while the second combines precision and recall for abstaining on unknown questions.

**Why it matters here:** The metric penalizes systems that improve abstention by refusing answerable questions or improve helpfulness by answering unknown questions.

**Lineage:** It aggregates the answer and abstention sides of the paper's abstention confusion matrix.
