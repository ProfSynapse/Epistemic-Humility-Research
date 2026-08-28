---
aliases:
- Cross-prediction introspection test
- Self-prediction versus cross-prediction control
- Other-model behavioral prediction baseline
tags:
- kg/method
- concept
- method
kg:
  id: method:cross-prediction-introspection-test
  type: method
  status: canonical
area: methods
related:
- '[[2410.13787--looking-inward-language-models-can-learn-about]]'
- '[[self-prediction-training]]'
- '[[self-prediction-advantage]]'
relationships:
- type: proposed_by
  target: '[[2410.13787--looking-inward-language-models-can-learn-about]]'
  target_id: paper:2410.13787
  confidence: high
- type: related_to
  target: '[[self-prediction-training]]'
  target_id: method:self-prediction-training
  confidence: high
- type: related_to
  target: '[[self-prediction-advantage]]'
  target_id: metric:self-prediction-advantage
  confidence: high
---

The cross-prediction test fine-tunes a target model and a different comparison
model on the same number and composition of examples about the target model's
behavior. Both then predict the target model on held-out tasks. A consistent
self-prediction advantage is treated as evidence unavailable from the shared
behavioral training examples alone.

**Why it matters here:** The comparison controls for learning general surface
patterns in the released behavioral labels.

**Lineage:** It is the main control for [[self-prediction-training]].
