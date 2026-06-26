---
aliases:
- Low Training Coverage Causes World Model Hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:low-coverage-causes-world-model-hallucination
  type: mechanism
  status: canonical
cause: Insufficient training data density in regions of the state-action space
effect: Hallucination events across all three modes (perceptual, action-marginalized, and scene-diverging) in world model rollouts
polarity: increases
related:
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
- '[[world-model-hallucination-modes]]'
- '[[state-action-coverage-gap]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
- type: related_to
  target: '[[world-model-hallucination-modes]]'
  target_id: term:world-model-hallucination-modes
- type: related_to
  target: '[[state-action-coverage-gap]]'
  target_id: term:state-action-coverage-gap
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

When a world model is trained on data that leaves portions of the state-action space sparsely covered, it encounters unfamiliar conditioning contexts during rollout and fails to generate coherent continuations, producing [[hallucination]] across all three [[world-model-hallucination-modes]]: perceptual errors, action-marginalized artifacts, and scene-diverging outputs (arXiv:2606.27326). The [[state-action-coverage-gap]] quantifies this deficit and predicts hallucination rate: regions with the lowest training density show the highest hallucination predictor scores. Filling coverage gaps through resampling is therefore the primary lever for reducing all three hallucination modes simultaneously.
