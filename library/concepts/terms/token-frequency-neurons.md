---
aliases:
- Token Frequency Neurons
- token frequency neuron
tags:
- kg/term
- concept
- term
kg:
  id: term:token-frequency-neurons
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[confidence-regulation-neurons]]'
relationships:
- type: proposed_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[confidence-regulation-neurons]]'
  target_id: term:confidence-regulation-neurons
  confidence: high
---

Token frequency neurons boost or suppress each vocabulary token's logit in
proportion to that token's log unigram frequency, shifting the model's output
distribution toward or away from the empirical token-frequency distribution of
its training corpus.

**Why it matters here:** Stolfo et al. discover and name this neuron class for
the first time, identifying it in Pythia 410M. Ablating token frequency
neurons substantially changes the KL divergence between the model's output and
the corpus unigram distribution relative to a frequency-direction-held-constant
baseline, making them the second of the two
[[confidence-regulation-neurons|confidence-regulation neuron]] classes studied
in the paper.

**Lineage:** no formal derivation edges recorded in this vault yet.
