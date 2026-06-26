---
aliases:
- hallucination-driven data collection
- targeted online data collection
- Curiosity-Driven Targeted Data Collection
tags:
- kg/method
- concept
- method
kg:
  id: method:curiosity-driven-targeted-data-collection
  type: method
  status: canonical
area: methods
related:
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
- '[[hallucination-predictor-world-model]]'
- '[[state-action-coverage-gap]]'
relationships:
- type: proposed_by
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
- type: derived_from
  target: '[[hallucination-predictor-world-model]]'
  target_id: method:hallucination-predictor-world-model
- type: related_to
  target: '[[state-action-coverage-gap]]'
  target_id: term:state-action-coverage-gap
---

An online data collection framework that uses world model hallucination predictors as curiosity rewards to guide exploration toward under-covered state-action regions. At each replanning step (every K=16 steps), candidate trajectories of horizon H=32 are rolled out in the world model, scored by predicted hallucination, and the highest-scoring trajectory is executed in the live environment. The collected data, by construction, covers transitions that previously caused hallucination, enabling adaptation to entirely unseen environments with as few as 50 real trajectories.

**Why it matters here:** This framework operationalizes epistemic humility in embodied agents: the system explicitly seeks out regions where its model is most likely wrong and updates accordingly, rather than acting confidently in the face of unknown unknowns. The connection between hallucination prediction and active data acquisition is a direct application of uncertainty-aware exploration.

**Lineage:** derives from [[hallucination-predictor-world-model]]; related to [[state-action-coverage-gap]]; introduced by [[2606.27326--hallucination-world-models-predictable-preventable]].
