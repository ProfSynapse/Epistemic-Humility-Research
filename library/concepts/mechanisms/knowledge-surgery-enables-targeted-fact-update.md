---
aliases:
- Knowledge Surgery Achieves Nontrivial Fact Update Success Without Fine-Tuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-surgery-enables-targeted-fact-update
  type: mechanism
  status: canonical
cause: Directly modifying FFN value-slot weight vectors for approximately 4 identified knowledge neurons per fact
effect: Fact update success rate of 34.4% with minimal collateral effect on other relations (inter-relation PPL increase of 7.2), versus 0.0% success for random neurons
polarity: enables
related:
- '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
- '[[knowledge-surgery]]'
- '[[knowledge-neurons]]'
- '[[model-editing]]'
relationships:
- type: supported_by
  target: '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
  target_id: paper:2104.08696
  confidence: high
- type: related_to
  target: '[[knowledge-surgery]]'
  target_id: method:knowledge-surgery
- type: related_to
  target: '[[knowledge-neurons]]'
  target_id: term:knowledge-neurons
- type: related_to
  target: '[[model-editing]]'
  target_id: method:model-editing
---

[[knowledge-surgery]] updates facts in BERT by directly modifying the FFN value vectors associated with the small set of identified [[knowledge-neurons]] for that fact, bypassing any gradient-based fine-tuning (arXiv:2104.08696). Editing approximately 4 neurons per fact achieves a 34.4% success rate on the update task while causing only a 7.2-perplexity increase on unrelated relations, demonstrating targeted modification without broad collateral damage. Randomly selected neurons of the same count yield 0% success, confirming that specificity of the intervention depends on the attribution-based neuron selection.
