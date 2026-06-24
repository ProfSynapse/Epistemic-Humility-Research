---
aliases:
- probing sparsity
- neuron sparsity
- sparse representation
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:representational-sparsity
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[sparse-probing]]'
- '[[superposition-hypothesis]]'
- '[[linear-probe]]'
relationships:
- type: related_to
  target: '[[sparse-probing]]'
  target_id: method:sparse-probing
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
---

Representational sparsity measures how few neurons are needed to accurately classify a feature in an LLM's activation space, operationalized as the minimum k in a k-sparse probe that achieves high F1 score. Lower k indicates a more localized representation; higher k indicates a more distributed one. Sparsity tends to increase on average with model scale but follows heterogeneous dynamics per feature type. It is a key empirical handle for distinguishing monosemantic from polysemantic representations.

**Why it matters here:** If abstention-relevant features (known vs. unknown) are sparsely represented, targeted interventions such as [[neuron-ablation]] or [[activation-intervention]] become more tractable and less likely to disrupt unrelated capabilities.

**Lineage:** quantifies the degree of [[superposition-hypothesis]] violation; measured via [[sparse-probing]] and related to [[linear-probe]] methods.
