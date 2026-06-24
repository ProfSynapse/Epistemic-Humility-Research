---
aliases:
- Mid-layer MLP modules mediate factual recall at subject tokens
- Mamba middle layers mediate factual recall at subject token
- mamba middle layers mediate subject factual recall
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:mid-layer-mlp-mediates-factual-recall
  type: mechanism
  status: canonical
cause: Processing of the final subject token in middle-layer feed-forward modules of GPT-style transformers
effect: Decisive contribution to the model's factual predictions, as shown by causal tracing -- restoring states only at these positions fully recovers correct factual output after corruption
polarity: enables
related:
- '[[2202.05262--rome-locating-editing-factual-associations]]'
- '[[2404.03646--locating-editing-factual-associations-mamba]]'
- '[[factual-recall-localization]]'
- '[[ffn-as-key-value-memory]]'
relationships:
- type: supported_by
  target: '[[2202.05262--rome-locating-editing-factual-associations]]'
  target_id: paper:2202.05262
  confidence: high
- type: supported_by
  target: '[[2404.03646--locating-editing-factual-associations-mamba]]'
  target_id: paper:2404.03646
  confidence: high
- type: related_to
  target: '[[factual-recall-localization]]'
  target_id: term:factual-recall-localization
- type: related_to
  target: '[[ffn-as-key-value-memory]]'
  target_id: term:ffn-as-key-value-memory
---

Causal tracing experiments in GPT-style transformers show that corrupting the subject tokens and then restoring activations at middle-layer MLP sublayers fully recovers the correct factual output, identifying these modules as the decisive locus of factual recall (arXiv:2202.05262). The same tracing methodology applied to Mamba reveals an analogous concentration of factual mediation in early-to-middle SSM layers at the final subject token (arXiv:2404.03646). This convergent finding across architectures supports the [[ffn-as-key-value-memory]] view, in which feed-forward weights store factual associations that attention mechanisms subsequently retrieve.
