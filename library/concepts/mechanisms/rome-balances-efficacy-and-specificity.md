---
aliases:
- ROME simultaneously achieves efficacy, generalization, and specificity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rome-balances-efficacy-and-specificity
  type: mechanism
  status: canonical
cause: Rank-one weight update targeting the decisive mid-layer MLP at the final subject token (identified by causal tracing)
effect: High composite Score (S=89.2 on GPT-2 XL; 91.5 on GPT-J), the best of all tested methods, combining ES=100%, PS=96.4%, and NS=75.4% -- unlike all baselines which sacrifice one dimension
polarity: enables
related:
- '[[2202.05262--rome-locating-editing-factual-associations]]'
- '[[rank-one-model-editing]]'
- '[[counterfact]]'
- '[[mid-layer-mlp-mediates-factual-recall]]'
relationships:
- type: supported_by
  target: '[[2202.05262--rome-locating-editing-factual-associations]]'
  target_id: paper:2202.05262
  confidence: high
- type: related_to
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
- type: related_to
  target: '[[counterfact]]'
  target_id: dataset:counterfact
- type: related_to
  target: '[[mid-layer-mlp-mediates-factual-recall]]'
  target_id: mechanism:mid-layer-mlp-mediates-factual-recall
---

[[rank-one-model-editing]] (ROME) uses causal tracing to identify the single mid-layer MLP most responsible for a factual association, then inserts the new fact via a rank-one weight update constrained to that layer (arXiv:2202.05262). Unlike fine-tuning, which achieves efficacy at the cost of specificity, or ROME-less baselines that fail on generalization, ROME achieves all three: ES=100%, paraphrase success PS=96.4%, and neighbor specificity NS=75.4% on CounterFact, yielding a composite Score of 89.2 on GPT-2 XL and 91.5 on GPT-J. This demonstrates that surgical causal targeting, rather than distributed gradient updates, is necessary to edit facts without collateral damage.
