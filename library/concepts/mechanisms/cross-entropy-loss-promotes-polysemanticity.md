---
aliases:
- Cross-Entropy Training Promotes Polysemanticity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:cross-entropy-loss-promotes-polysemanticity
  type: mechanism
  status: canonical
cause: Training neural networks on cross-entropy loss with sparse activations
effect: Individual neurons become polysemantic even without superposition, because ambiguous multi-concept representations achieve lower loss than single-concept monosemantic ones
polarity: increases
related:
- '[[tc2023--towards-monosemanticity]]'
- '[[polysemanticity]]'
- '[[superposition-hypothesis]]'
- '[[monosemanticity]]'
relationships:
- type: supported_by
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
- type: related_to
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
---

Bricken et al. (tc2023) demonstrate that cross-entropy loss on language modeling directly incentivizes polysemanticity: a neuron that responds to multiple unrelated concepts can produce lower expected loss than one dedicated to a single concept, because the training signal rewards any feature correlation that predicts the next token. This mechanism operates even in the absence of superposition geometry, implying that polysemanticity is a fundamental pressure of standard language model training rather than purely a capacity side-effect.
