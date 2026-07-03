---
aliases:
- SALAD-Bench
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:saladbench
  type: dataset
  status: canonical
area: datasets
related: []
relationships: []
---

SALAD-Bench is a hierarchical safety benchmark for large language models that organizes harmful-request evaluation across a taxonomy of risk categories (physical harm, privacy violation, hate speech, etc.) at multiple levels of granularity. It provides a large, structured test set of harmful prompts paired with human-annotated ground truth on whether a model response constitutes a refusal, enabling precise measurement of refusal rates and attack-success rates across categories. Its hierarchical structure allows researchers to distinguish coarse-grained safety failures from fine-grained category-specific gaps.

**Why it matters here:** Refusal behavior is a key axis of epistemic humility: a model that refuses appropriately on unanswerable or unsafe queries demonstrates calibrated scope-awareness. SALAD-Bench provides a standardized surface for measuring whether steering interventions that improve epistemic outputs also preserve or improve safety refusals.

**Lineage:** a standalone benchmark; no direct methodological lineage.
