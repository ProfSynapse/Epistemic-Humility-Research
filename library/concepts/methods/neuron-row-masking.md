---
aliases:
- neuron-row zeroing
- one-shot neuron-row zeroing
- row masking
- row ablation
tags:
- kg/method
- concept
- method
kg:
  id: method:neuron-row-masking
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[neuron-ablation]]'
- '[[causal-intervention]]'
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
relationships:
- type: variation_of
  target: '[[neuron-ablation]]'
  target_id: method:neuron-ablation
  confidence: high
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: high
- type: used_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
---

Neuron-row masking is an intervention that zeros a selected output row of a transformer projection or feed-forward matrix, removing that row's contribution across tokens in a forward pass. Unlike activation patching, which swaps activations between clean and corrupted contexts, row masking directly removes a structural unit chosen by a selector.

**Why it matters here:** Row masking makes selector claims falsifiable. If a selector says a row is irrelevant, masking it should preserve language modeling or target behavior; if it says a row is important, masking it should produce a measurable degradation or behavioral shift.

**Lineage:** a row-level form of [[neuron-ablation]] and [[causal-intervention]] used by [[neuron-selector-causal-audit]].
