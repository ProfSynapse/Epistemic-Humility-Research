---
aliases:
- Ik-Ik rate
- Ik-Idk rate
- Idk-Ik rate
- Idk-Idk rate
- Truthful rate
- knowledge quadrant
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:knowledge-quadrant-metric
  type: metric
  status: canonical
area: metrics
related:
- '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
- '[[abstention-rate]]'
- '[[idk-dataset]]'
- '[[ik-threshold]]'
relationships:
- type: proposed_by
  target: '[[2401.13275--can-ai-assistants-know-what-they-dont-know]]'
  target_id: paper:2401.13275
  confidence: high
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
- type: related_to
  target: '[[idk-dataset]]'
  target_id: dataset:idk-dataset
- type: related_to
  target: '[[ik-threshold]]'
  target_id: term:ik-threshold
---

The knowledge-quadrant metric cross-tabulates ground-truth knowledge (does the
model actually know the question?) with the model's behavioral choice (answer or
refuse) to produce four rates: Ik-Ik (answered a known question correctly),
Ik-Idk (correctly refused an unknown question), Idk-Ik (over-refused a known
question), and Idk-Idk (answered an unknown question, i.e., hallucinated). The
aggregate "Truthful rate" sums Ik-Ik and Ik-Idk and serves as the primary
evaluation criterion.

**Why it matters here:** The quadrant decomposition disentangles over-refusal
from under-refusal, which is exactly the precision-recall tension the Phase 1
experiment probes when comparing SFT, DPO, and KTO on abstention.

**Lineage:** proposed in [[2401.13275--can-ai-assistants-know-what-they-dont-know]];
complements [[abstention-rate]] by conditioning on ground-truth knowledge.
