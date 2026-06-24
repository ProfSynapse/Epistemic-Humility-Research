---
aliases:
- scale emergence threshold on MMLU
- MMLU scale threshold
- near-chance below 13B on MMLU
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:scale-threshold-for-above-chance-mmlu-accuracy
  type: mechanism
  status: canonical
cause: "Increasing GPT-3 model size from 2.7B through 6.7B and 13B to 175B parameters, evaluated few-shot on the 57-subject MMLU benchmark"
effect: "Accuracy remains near random chance (25-26%) for all models up to and including 13B, then rises to 43.9% at 175B, indicating a sharp discontinuity rather than a smooth scaling curve for multitask academic knowledge"
polarity: enables
related:
- '[[2009.03300--mmlu-benchmark]]'
- '[[mmlu]]'
- '[[model-size-improves-calibration]]'
- '[[model-scale-improves-self-knowledge]]'
- '[[dominant-uncertainty-source-shifts-with-model-scale]]'
- '[[gpt-3]]'
relationships:
- type: supported_by
  target: '[[2009.03300--mmlu-benchmark]]'
  target_id: paper:2009.03300
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
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
  target: '[[dominant-uncertainty-source-shifts-with-model-scale]]'
  target_id: mechanism:dominant-uncertainty-source-shifts-with-model-scale
  confidence: high
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
  confidence: high
---

Below 13B parameters, GPT-3 models lack sufficient parametric knowledge to answer MMLU questions above chance regardless of the few-shot prompt format. The 175B model crosses a threshold where accumulated pretraining knowledge begins to support reliable retrieval across diverse academic subjects. The threshold is not smooth: Table 1 shows 25.9%, 24.9%, 26.0% for the 2.7B, 6.7B, and 13B models respectively, then a jump to 43.9% at 175B. This emergent threshold pattern is consistent with the broader scaling literature on emergent capabilities but is documented here specifically for multitask knowledge breadth rather than narrow skill tasks.
