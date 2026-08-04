---
aliases:
- Confidence Regulation Neurons
- confidence-regulation neurons
tags:
- kg/term
- concept
- term
kg:
  id: term:confidence-regulation-neurons
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[entropy-neurons]]'
- '[[token-frequency-neurons]]'
- '[[calibration]]'
relationships:
- type: proposed_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[entropy-neurons]]'
  target_id: term:entropy-neurons
  confidence: high
- type: related_to
  target: '[[token-frequency-neurons]]'
  target_id: term:token-frequency-neurons
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
---

Confidence regulation neurons is Stolfo et al.'s umbrella term for MLP neurons
whose function is to modulate a language model's next-token uncertainty
directly, rather than to encode task-relevant content. The paper studies two
such classes: [[entropy-neurons]], which flatten or sharpen the whole output
distribution via the final LayerNorm, and [[token-frequency-neurons]], which
push the output toward or away from the corpus unigram distribution.

**Why it matters here:** This term names the paper's central object of study:
components that a model uses to actively manage its own predictive confidence,
independent of the content-level computation that produced the underlying
logits.

**Lineage:** introduced by this paper as the umbrella over its two proposed
neuron classes.
