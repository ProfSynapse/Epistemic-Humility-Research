---
aliases:
- Hallucination Predictors as Curiosity Rewards Enable Efficient Adaptation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:hallucination-predictors-enable-efficient-adaptation
  type: mechanism
  status: canonical
cause: Scoring candidate world-model rollouts by predicted hallucination and executing the highest-ranked trajectory in the live environment
effect: Rapid adaptation of a pretrained world model to entirely unseen environments with minimal real data
polarity: enables
related:
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
- '[[hallucination-predictor-world-model]]'
- '[[curiosity-driven-targeted-data-collection]]'
- '[[coverage-aware-training]]'
relationships:
- type: supported_by
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
- type: related_to
  target: '[[hallucination-predictor-world-model]]'
  target_id: method:hallucination-predictor-world-model
- type: related_to
  target: '[[curiosity-driven-targeted-data-collection]]'
  target_id: method:curiosity-driven-targeted-data-collection
- type: related_to
  target: '[[coverage-aware-training]]'
  target_id: method:coverage-aware-training
---

[[hallucination-predictor-world-model]] scores can be repurposed as curiosity-style rewards: by selecting the rollout with the highest predicted hallucination as the next real-environment query, the agent preferentially collects data in the least-covered state-action regions (arXiv:2606.27326). This [[curiosity-driven-targeted-data-collection]] strategy achieves substantially faster reduction in hallucination rates than random data collection, enabling a pretrained world model to generalize to unseen environments with far fewer environment interactions. The result demonstrates that the same predictors used to diagnose hallucination can actively guide the data-gathering process that cures it.
