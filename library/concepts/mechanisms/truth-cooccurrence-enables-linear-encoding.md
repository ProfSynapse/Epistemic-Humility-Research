---
aliases:
- Truth Co-occurrence Enables Linear Truth Encoding
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:truth-cooccurrence-enables-linear-encoding
  type: mechanism
  status: canonical
cause: "Training data in which true statements co-occur with true statements and false with false, giving the model a loss-reduction incentive to track a latent truth variable via the [[truth-co-occurrence-hypothesis]]"
effect: "A linear [[truth-direction|truth subspace]] emerges in the transformer's [[residual-stream]], separating true from false hidden-state representations"
polarity: enables
related:
- '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
- '[[truth-co-occurrence-hypothesis]]'
- '[[truth-direction]]'
- '[[linear-representation-hypothesis]]'
relationships:
- type: supported_by
  target: '[[2510.15804--emergence-linear-truth-encodings-language-models]]'
  target_id: paper:2510.15804
  confidence: high
- type: related_to
  target: '[[truth-co-occurrence-hypothesis]]'
  target_id: term:truth-co-occurrence-hypothesis
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

When the training corpus clusters true statements together and false statements together, a model minimising cross-entropy loss gains a free source of loss reduction by learning to track which truth-value cluster a sentence belongs to. This implicit label structure creates a gradient incentive to encode a linear truth variable in the residual stream, which the truth-encodings paper (arXiv:2510.15804) confirms experimentally by showing that a linear probe trained on toy corpora with controlled co-occurrence structure successfully separates true from false hidden states. The mechanism implies that linear truth encodings are a natural consequence of realistic corpus statistics rather than a property requiring special training.
