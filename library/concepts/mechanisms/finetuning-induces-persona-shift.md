---
aliases:
- Finetuning induces activation shift along persona vectors
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:finetuning-induces-persona-shift
  type: mechanism
  status: canonical
cause: "Training on trait-expressing or domain-flawed data shifting model activations along [[persona-vectors]] directions"
effect: "Elevated post-finetuning behavioural expression of the corresponding trait and, sometimes, unintended cross-trait spillover to related persona dimensions"
polarity: increases
related:
- '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
- '[[persona-vectors]]'
- '[[supervised-finetuning]]'
- '[[trait-expression-delta]]'
relationships:
- type: supported_by
  target: '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
  target_id: paper:2507.21509
  confidence: high
- type: related_to
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
- type: related_to
  target: '[[trait-expression-delta]]'
  target_id: metric:trait-expression-delta
---

Fine-tuning on data that exemplifies a specific character trait (e.g., dishonesty, sycophancy) shifts the model's final prompt-token activations toward the corresponding persona vector as measured by cosine projection. This shift predicts increased behavioural expression of the target trait on held-out evaluation prompts (arXiv:2507.21509). Unintended cross-trait spillover can also occur when the trained and untrained traits share a nearby direction in the persona vector space, highlighting that persona directions are not perfectly orthogonal and fine-tuning interventions may have off-target effects.
