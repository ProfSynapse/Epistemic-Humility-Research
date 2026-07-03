---
aliases:
- projection difference metric
- pre-finetuning persona signal
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:projection-difference
  type: metric
  status: canonical
area: steering
related:
- '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
- '[[persona-vectors]]'
- '[[preventative-steering]]'
relationships:
- type: proposed_by
  target: '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
  target_id: paper:2507.21509
  confidence: high
- type: related_to
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
---

The projection difference metric is the difference between the average projection of training-set response activations onto a persona vector and the average projection of the base model's natural responses to the same prompts. A large positive value signals that the corpus contains stronger trait signal than the model's default behavior, and empirically predicts a corresponding post-finetuning shift in trait expression proportional to that gap. Because the metric is computed entirely before any training, it enables dataset screening and risk-ranking without running gradient steps.

**Why it matters here:** When constructing calibration or abstention training sets, projection difference offers a cheap pre-flight check for whether a data batch will inadvertently push the model toward overconfidence or sycophancy, supporting principled dataset curation rather than post-hoc behavior audits.

**Lineage:** derived from [[persona-vectors]] as the underlying directional basis; supports the [[preventative-steering]] workflow by identifying high-trait-signal batches before training begins.
