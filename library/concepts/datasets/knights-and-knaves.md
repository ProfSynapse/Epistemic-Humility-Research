---
aliases:
- K&K puzzles
- knights knaves dataset
- LogicRL puzzles
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:knights-and-knaves
  type: dataset
  status: canonical
area: datasets
related:
- '[[2511.11500--reinforced-hesitation]]'
- '[[reinforced-hesitation]]'
- '[[abstention]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: proposed_by
  target: '[[2511.11500--reinforced-hesitation]]'
  target_id: paper:2511.11500
  confidence: high
- type: related_to
  target: '[[reinforced-hesitation]]'
  target_id: method:reinforced-hesitation
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
---

A dataset of combinatorial logic puzzles where a set of inhabitants are either truth-telling knights or lying knaves, and the solver must determine each inhabitant's type from their statements. The RH paper uses 80,000 training and 10,000 test samples of 5, 6, and 7-person puzzles with a 2:1 easy-to-hard ratio based on logical complexity; puzzle difficulty scales exponentially with inhabitant count.

**Why it matters here:** Provides clean ground-truth verification for abstention decisions and natural difficulty stratification (easy vs. hard) that reveals whether trained models learn to calibrate abstention to problem complexity rather than abstaining uniformly.

**Lineage:** Used in the LogicRL line of work (Xie et al. 2025); adopted by RH (2511.11500) as the controlled training and evaluation domain for all Pareto frontier and cascading experiments.
