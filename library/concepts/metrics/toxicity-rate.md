---
aliases:
- Toxicity rate
- Toxic generation rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:toxicity-rate
  type: metric
  status: canonical
area: metrics
related:
- '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
- '[[auroc]]'
relationships:
- type: used_by
  target: '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
  target_id: paper:2510.21531
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
---

Toxicity rate is the fraction of generated responses whose classifier score is
at least 0.5. The paper computes it on 100 held-out toxic prompts.

**Why it matters here:** It distinguishes changes in output behavior from
changes in the internal probe's discrimination performance.

**Lineage:** The paper reports it alongside probe [[auroc]].
