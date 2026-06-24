---
aliases:
- scale-dependent uncertainty dominance
- uncertainty source shift with scale
- model size modulates dominant UQ component
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dominant-uncertainty-source-shifts-with-model-scale
  type: mechanism
  status: canonical
cause: "Increasing model scale (number of parameters) and task type (factual QA vs mathematical reasoning)"
effect: "The dominant uncertainty source shifts: smaller models show decoding randomness as the strongest failure predictor; larger models show input ambiguity as the strongest predictor; knowledge-gap uncertainty is task-dependent and near-chance on open-domain factual QA"
polarity: mediates
related:
- '[[2603.24967--uncertainty-source-decomposition]]'
- '[[uncertainty-source-decomposition]]'
- '[[input-ambiguity]]'
- '[[decoding-randomness]]'
- '[[knowledge-gap]]'
- '[[model-size-improves-calibration]]'
- '[[model-scale-improves-self-knowledge]]'
- '[[larger-model-better-abstention]]'
relationships:
- type: supported_by
  target: '[[2603.24967--uncertainty-source-decomposition]]'
  target_id: paper:2603.24967
  confidence: high
- type: related_to
  target: '[[uncertainty-source-decomposition]]'
  target_id: method:uncertainty-source-decomposition
  confidence: high
- type: related_to
  target: '[[input-ambiguity]]'
  target_id: term:input-ambiguity
  confidence: high
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: high
- type: related_to
  target: '[[knowledge-gap]]'
  target_id: term:knowledge-gap
  confidence: high
- type: related_to
  target: '[[model-size-improves-calibration]]'
  target_id: mechanism:model-size-improves-calibration
  confidence: high
- type: related_to
  target: '[[model-scale-improves-self-knowledge]]'
  target_id: mechanism:model-scale-improves-self-knowledge
  confidence: high
- type: related_to
  target: '[[larger-model-better-abstention]]'
  target_id: mechanism:larger-model-better-abstention
  confidence: high
---

Across the Gemma 3 family (1B to 27B) on TriviaQA, decoding randomness (U_dec) is the strongest failure predictor for the 1B model, while input ambiguity (U_input AUROC 0.761) becomes dominant at 27B. Knowledge-gap uncertainty hovers near chance (AUROC 0.499) on TriviaQA for both Llama 3 8B and Gemma 3 27B, but rises to 0.598 for Llama 3 8B on GSM8K. The paper notes no strictly monotonic trend across all Gemma 3 sizes, so model scale is a modulator rather than a deterministic predictor of which source dominates. The mechanism implies that post-training interventions targeting uncertainty should be calibrated to the model's scale and task regime, not applied uniformly.
