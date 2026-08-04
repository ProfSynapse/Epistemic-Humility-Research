---
aliases:
- Entropy Neurons Hedge Against Confident Induction Errors
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:entropy-neurons-hedge-against-confident-induction-errors
  type: mechanism
  status: canonical
cause: An entropy neuron activates during the repeated portion of a duplicated sequence, driven by induction-head activity
effect: Output entropy on the repeated tokens rises (mean-ablating the neuron reduces entropy by up to 70%), tempering the model's confidence in its induction-based predictions and hedging against confidently-wrong continuations
polarity: increases
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[entropy-neurons]]'
- '[[induction-heads]]'
relationships:
- type: supported_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[entropy-neurons]]'
  target_id: term:entropy-neurons
  confidence: high
- type: related_to
  target: '[[induction-heads]]'
  target_id: term:induction-heads
  confidence: high
---

Stolfo et al.'s induction case study argues entropy neurons actively manage
confidence during induction rather than merely reflecting it: mean-ablating
entropy neuron 11.2378 during the repeated portion of duplicated 200-token
sequences reduces output entropy by up to 70%, indicating the neuron's normal
activation is hedging against overconfident induction predictions, which is
useful because the induction heuristic ("repeat what followed this token
before") is not always correct.
