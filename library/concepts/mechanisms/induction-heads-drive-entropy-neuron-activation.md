---
aliases:
- Induction Heads Drive Entropy Neuron Activation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:induction-heads-drive-entropy-neuron-activation
  type: mechanism
  status: canonical
cause: Induction heads (L5H1, L5H5, L6H9 in GPT-2 Small) attend to the BOS token during repeated subsequences, supplying the signal that activates a downstream entropy neuron
effect: BOS-ablating those induction heads substantially reduces the entropy neuron's activation during induction
polarity: enables
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[induction-heads]]'
- '[[entropy-neurons]]'
relationships:
- type: supported_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[induction-heads]]'
  target_id: term:induction-heads
  confidence: high
- type: related_to
  target: '[[entropy-neurons]]'
  target_id: term:entropy-neurons
  confidence: high
---

In GPT-2 Small's induction case study, Stolfo et al. show that the top three
induction heads causally drive the activation of entropy neuron 11.2378:
BOS-ablating L5H1, L5H5, and L6H9 substantially reduces the neuron's
activation on repeated 200-token sequences, establishing a causal path from
induction-head firing to entropy-neuron engagement.
