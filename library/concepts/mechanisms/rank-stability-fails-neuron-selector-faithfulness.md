---
aliases:
- stable selector rankings can be causally invalid
- rank stability does not imply selector faithfulness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rank-stability-fails-neuron-selector-faithfulness
  type: mechanism
  status: canonical
cause: "Selector rankings are evaluated by cross-batch rank stability rather than by row-level intervention"
effect: "A selector such as [[mean-activation-neuron-selector]] can appear reliable while failing to identify rows whose masking has the predicted causal effect"
polarity: complicates
area: mechanistic-interpretability
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[mean-activation-neuron-selector]]'
- '[[selector-causal-faithfulness]]'
- '[[neuron-selector-causal-audit]]'
relationships:
- type: supported_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
  evidence:
  - Table 1
- type: related_to
  target: '[[mean-activation-neuron-selector]]'
  target_id: method:mean-activation-neuron-selector
  confidence: high
- type: related_to
  target: '[[selector-causal-faithfulness]]'
  target_id: metric:selector-causal-faithfulness
  confidence: high
- type: related_to
  target: '[[neuron-selector-causal-audit]]'
  target_id: method:neuron-selector-causal-audit
  confidence: high
---

Rank stability can fail as evidence of mechanistic faithfulness because stable salience rankings may track persistent correlations or activation magnitude rather than causal contribution. Faithfulness to Refusal shows this with MeanActivation on LLaMA-3.1-8B: the selector has very high Spearman/Jaccard stability but performs poorly in LeRF/MoRF causal audits compared with IG, LRP, and Consensus-2.

**Implication:** Stable abstention or refusal probes should not be treated as mechanistic evidence until they predict intervention effects under matched controls.
