---
aliases:
- contrastive row masks install refusal
- row-specific refusal installation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:contrastive-row-masks-install-refusal
  type: mechanism
  status: canonical
cause: "A [[contrastive-refusal-mask]] selects attribution-ranked rows from harmful-vs-benign refusal contrasts and masks them in an instruction-tuned model"
effect: "The model's refusal rate rises on harmful hate/crime prompts with low benign over-refusal, while layer-matched random controls at the same depths fail to reproduce the effect"
polarity: positive
area: mechanistic-interpretability
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[contrastive-refusal-mask]]'
- '[[cast-refusal-benchmark]]'
- '[[or-bench]]'
- '[[sorrybench]]'
relationships:
- type: supported_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
  evidence:
  - Table 2
  - Table 45
- type: related_to
  target: '[[contrastive-refusal-mask]]'
  target_id: method:contrastive-refusal-mask
  confidence: high
- type: related_to
  target: '[[cast-refusal-benchmark]]'
  target_id: dataset:cast-refusal-benchmark
  confidence: high
- type: related_to
  target: '[[or-bench]]'
  target_id: dataset:or-bench
  confidence: high
- type: related_to
  target: '[[sorrybench]]'
  target_id: dataset:sorrybench
  confidence: high
---

Contrastive attribution can identify row sets that causally install refusal behavior rather than merely detecting harmful prompts. Faithfulness to Refusal shows this most clearly for hate and crime domains, where LRP/IG/Consensus-2 masks raise harmful refusal, keep CAST benign over-refusal low, and outperform layer-matched random controls.

**Implication:** For refusal and abstention interventions, behavior gains should be paired with specificity controls so the edit is not explained by depth, model damage, or broad refusal drift.
