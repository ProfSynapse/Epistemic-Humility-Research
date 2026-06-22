---
aliases:
- Suppressing Knowledge Neurons Reduces Factual Expression
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-neuron-suppression-reduces-fact-expression
  type: mechanism
  status: canonical
cause: Setting activations of identified knowledge neurons to zero (suppression)
effect: Correct-answer probability decreases by 29.03% on average across relations in BERT-base-cased on ParaRel
polarity: decreases
related:
- '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
- '[[knowledge-neurons]]'
- '[[pararel]]'
- '[[integrated-gradients]]'
relationships:
- type: supported_by
  target: '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
  target_id: paper:2104.08696
  confidence: high
- type: related_to
  target: '[[knowledge-neurons]]'
  target_id: term:knowledge-neurons
- type: related_to
  target: '[[pararel]]'
  target_id: dataset:pararel
- type: related_to
  target: '[[integrated-gradients]]'
  target_id: method:integrated-gradients
---

[[knowledge-neurons]] are identified by an integrated-gradients attribution method that scores each FFN neuron by its contribution to expressing a specific factual relation across multiple paraphrase prompts (arXiv:2104.08696). Zeroing out the activations of the small set of neurons identified for a given fact reduces the correct-answer probability by 29.03% on average across relations in BERT-base-cased evaluated on [[pararel]], while suppressing random neurons of equal size causes negligible degradation. This causal test establishes that the identified neurons are not merely correlated with fact expression but functionally necessary for it.
