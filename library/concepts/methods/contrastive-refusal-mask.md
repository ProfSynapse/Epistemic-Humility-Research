---
aliases:
- contrastive refusal row mask
- harmful-benign refusal mask
- CAST refusal mask
tags:
- kg/method
- concept
- method
kg:
  id: method:contrastive-refusal-mask
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[contrastive-activation-addition]]'
- '[[neuron-row-masking]]'
- '[[cast-refusal-benchmark]]'
relationships:
- type: proposed_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
- type: related_to
  target: '[[contrastive-activation-addition]]'
  target_id: method:contrastive-activation-addition
  confidence: medium
- type: uses
  target: '[[neuron-row-masking]]'
  target_id: method:neuron-row-masking
  confidence: high
- type: uses
  target: '[[cast-refusal-benchmark]]'
  target_id: dataset:cast-refusal-benchmark
  confidence: high
---

A contrastive refusal mask selects neuron rows using a harmful-vs-benign contrast over refusal-onset and compliance-onset token scores, then masks rows to install or amplify refusal behavior. In Faithfulness to Refusal, the mask is calibrated against benign over-refusal and perplexity constraints rather than optimizing harmful refusal alone.

**Why it matters here:** The method exposes whether an internal selector can change refusal behavior causally without simply making the model broadly worse or more blanket-refusal prone. It is a template for auditing abstention/refusal interventions in epistemic-humility experiments.

**Lineage:** proposed in [[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]; conceptually related to [[contrastive-activation-addition]] but implemented through [[neuron-row-masking]].
