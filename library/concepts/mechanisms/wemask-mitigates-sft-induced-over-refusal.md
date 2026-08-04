---
aliases:
- WeMask mitigates SFT-induced over-refusal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:wemask-mitigates-sft-induced-over-refusal
  type: mechanism
  status: canonical
cause: "applying weight-guided masking (WeMask) during or alongside fine-tuning moderately attenuates the attention sink that forms in the layer immediately after the ME Layer, without eliminating it."
effect: "over-refusal induced by fine-tuning is reduced on safety-alignment benchmarks (e.g. XSTest), and this partial rather than complete sink attenuation is associated with the best downstream performance."
polarity: prevents
related:
- '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
- '[[weight-guided-masking]]'
- '[[attention-sink]]'
- '[[xstest]]'
relationships:
- type: supported_by
  target: '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
  target_id: paper:2605.08504
  confidence: medium
- type: related_to
  target: '[[weight-guided-masking]]'
  target_id: method:weight-guided-masking
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
- type: related_to
  target: '[[xstest]]'
  target_id: dataset:xstest
  confidence: medium
---

Shi et al. find that attention sinks emerge in the layer immediately
following the ME Layer and reflect a low-rank, massive-activation-induced
representation collapse rather than a pure softmax artifact. WeMask does not
eliminate this sink but moderately attenuates it, and that partial (not
complete) attenuation is associated with the best performance, including
reduced over-refusal on safety-alignment benchmarks such as XSTest after
fine-tuning.

**Lineage:** established by
[[2605.08504--single-layer-explain-them-all-understanding-massive]]; a
downstream safety-behavior consequence of [[weight-guided-masking]] acting on
the [[attention-sink]] that forms after the ME Layer, evaluated on
[[xstest]].
