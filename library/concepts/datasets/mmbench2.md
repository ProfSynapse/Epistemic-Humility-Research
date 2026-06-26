---
aliases:
- MMBench 2
- Massively Multitask Visual World Modeling Benchmark 2
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:mmbench2
  type: dataset
  status: canonical
area: datasets
related:
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
relationships:
- type: proposed_by
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
---

A 427-hour, 210-task benchmark for visual world modeling comprising 65,600 trajectories at 224x224 resolution across 10 domains (DMControl, ManiSkill3, Meta-World, MuJoCo, MiniArcade, Box2D, RoboDesk, OGBench, Continuous Atari, DMControl Extended). Ground-truth action and reward labels, live environments, and language instructions are provided; 200 tasks form the pretraining corpus and 10 are held out as unseen transfer tasks. Mixed-quality trajectories including human play data extend earlier visual world modeling benchmarks with broader behavioral coverage.

**Why it matters here:** MMBench2 operationalizes world-model hallucination as coverage gaps in training data, making it a concrete testbed for coverage-aware training and hallucination-predictor hypotheses that bear on epistemic humility in embodied agents.

**Lineage:** proposed in [[2606.27326--hallucination-world-models-predictable-preventable]].
