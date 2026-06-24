---
aliases:
- DPO asymmetry from upstream collapse
- collapsed SFT limits DPO diversity loss
- DPO mode-seeking operates on residual spread
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-diversity-cost-depends-on-upstream-sft-state
  type: mechanism
  status: canonical
cause: "DPO's reverse-KL objective is mode-seeking; its gradient is proportional to the implicit reward gap between chosen and rejected outputs, which is small when the model is already collapsed"
effect: "When the upstream SFT model is already collapsed (Think lineage), DPO erases only -4% further diversity; when the upstream SFT model retains residual spread (Instruct lineage), DPO erases -23%; the effect is largest on summarization and code-reasoning tasks where Instruct-SFT had preserved substantial diversity"
polarity: decreases
related:
- '[[2604.16027--posttraining-diversity-collapse]]'
- '[[output-diversity-collapse]]'
- '[[direct-preference-optimization]]'
- '[[dpo-choice-induces-severe-answer-uncertainty-shift]]'
- '[[narrow-sft-data-collapses-output-diversity]]'
- '[[preference-collapse-causes-alignment-overconfidence]]'
relationships:
- type: supported_by
  target: '[[2604.16027--posttraining-diversity-collapse]]'
  target_id: paper:2604.16027
  confidence: high
- type: related_to
  target: '[[output-diversity-collapse]]'
  target_id: term:output-diversity-collapse
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[dpo-choice-induces-severe-answer-uncertainty-shift]]'
  target_id: mechanism:dpo-choice-induces-severe-answer-uncertainty-shift
  confidence: high
- type: related_to
  target: '[[narrow-sft-data-collapses-output-diversity]]'
  target_id: mechanism:narrow-sft-data-collapses-output-diversity
  confidence: high
- type: related_to
  target: '[[preference-collapse-causes-alignment-overconfidence]]'
  target_id: mechanism:preference-collapse-causes-alignment-overconfidence
  confidence: high
---

The same DPO data pool and objective produce different diversity outcomes depending on the upstream SFT state. When Think enters DPO already at its diversity floor, chosen and rejected responses are both near the mode, yielding small gradients and minimal further compression. When Instruct enters DPO with residual spread, DPO aggressively downweights the tails. On three math/code tasks, Think-DPO actually increases diversity slightly, and Instruct-DPO does the same on GSM8K, suggesting DPO can partially correct a collapsed SFT distribution. This result shows DPO's diversity cost is not intrinsic to the objective but is mediated by the upstream state the SFT stage left.
