---
aliases:
- arousal steering controls behavior
- arousal-refusal coupling
- arousal monotonic behavioral control
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:arousal-axis-monotonically-controls-refusal-and-sycophancy
  type: mechanism
  status: canonical
cause: "Steering LLM activations along the arousal axis of the VA subspace (increasing or decreasing arousal coordinate)."
effect: "Refusal rate and sycophancy rate shift near-monotonically and in opposite directions: lowering arousal raises refusal and lowers sycophancy; raising arousal lowers refusal and raises sycophancy."
polarity: mediates
related:
- '[[2604.03147--sycophancy-internal-representations]]'
- '[[lexical-mediation-links-va-steering-to-behavioral-control]]'
- '[[valence-arousal-subspace]]'
- '[[va-subspace-extraction]]'
- '[[refusal-direction-mediates-refusal]]'
- '[[sycophancy]]'
- '[[safety-refusal]]'
- '[[steering-vector]]'
relationships:
- type: supported_by
  target: '[[2604.03147--sycophancy-internal-representations]]'
  target_id: paper:2604.03147
  confidence: high
- type: related_to
  target: '[[lexical-mediation-links-va-steering-to-behavioral-control]]'
  target_id: mechanism:lexical-mediation-links-va-steering-to-behavioral-control
  confidence: high
- type: related_to
  target: '[[valence-arousal-subspace]]'
  target_id: term:valence-arousal-subspace
  confidence: high
- type: related_to
  target: '[[va-subspace-extraction]]'
  target_id: method:va-subspace-extraction
  confidence: high
- type: related_to
  target: '[[refusal-direction-mediates-refusal]]'
  target_id: mechanism:refusal-direction-mediates-refusal
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: high
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

On Llama-3.1-8B, decreasing arousal (alpha=-0.45) raises OKTest refusal from 20% to 86% and XSTest refusal from 8% to 86%, while increasing arousal (alpha=+0.45) reduces HarmBench refusal from 87% to 5%. Sycophancy on Political Typology drops from 78% to 61% at alpha=-0.30 and rises to 84% at alpha=+0.30. Random steering directions remain within 2-3pp of baseline across all alpha values, confirming the effect is axis-specific. The arousal axis is nearly orthogonal to the contrastive refusal direction (86.5 degrees) yet achieves comparable or stronger behavioral control, indicating a distinct mechanistic pathway (see lexical-mediation-links-va-steering-to-behavioral-control). Effects replicate on Qwen3-8B and Qwen3-14B.
