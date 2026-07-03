---
aliases:
- multitask learning
- MTL
- multi-task classification
- Multi-Task Learning
tags:
- kg/method
- concept
- method
kg:
  id: method:multi-task-learning
  type: method
  status: canonical
area: methods
related:
- '[[disentangled-representation]]'
relationships:
- type: related_to
  target: '[[disentangled-representation]]'
  target_id: term:disentangled-representation
---

Multi-task learning trains a single model simultaneously across multiple related tasks
while sharing internal representations rather than learning each task in isolation. A key
theoretical result is that when the number of tasks N_task exceeds the input
dimensionality D, any optimal multi-task classifier is provably forced to learn a
disentangled representation of the latent factors underlying the tasks, because no
single-factor shortcut can satisfy all tasks at once. The resulting shared representations
often support generalization to task combinations and contexts not seen during training.

**Why it matters here:** Multi-task training pressure across distinct epistemic conditions
(knowns, unknowns, ambiguous inputs) may be the mechanism that induces the disentangled
internal representations required for principled abstention and calibrated confidence,
rather than each behavior being learned independently.

**Lineage:** related to [[disentangled-representation]], which is the structural outcome
this method provably produces under sufficient task diversity.
