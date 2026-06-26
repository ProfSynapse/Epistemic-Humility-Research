---
aliases:
- Coverage-Aware Sampling Reduces All Hallucination Modes Simultaneously
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:coverage-aware-sampling-reduces-hallucination
  type: mechanism
  status: canonical
cause: Task-uniform data resampling applied to both tokenizer and dynamics model training
effect: All three normalized hallucination predictor values and rollout ΔPSNR
polarity: decreases
related:
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
- '[[coverage-aware-training]]'
- '[[hallucination-predictor-world-model]]'
- '[[world-model-hallucination-modes]]'
relationships:
- type: supported_by
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
- type: related_to
  target: '[[coverage-aware-training]]'
  target_id: method:coverage-aware-training
- type: related_to
  target: '[[hallucination-predictor-world-model]]'
  target_id: method:hallucination-predictor-world-model
- type: related_to
  target: '[[world-model-hallucination-modes]]'
  target_id: term:world-model-hallucination-modes
---

[[coverage-aware-training]] resamples training trajectories to equalize representation across tasks and action distributions, directly closing the [[state-action-coverage-gap]] that drives all three [[world-model-hallucination-modes]] (arXiv:2606.27326). After resampling, all three [[hallucination-predictor-world-model]] scores (u_r, u_f, u_s) decrease and rollout ΔPSNR improves, confirming that coverage rather than total data volume is the controlling factor. The effect is observed jointly for perceptual, action-marginalized, and scene-diverging hallucination, indicating a single root cause amenable to a single intervention.
