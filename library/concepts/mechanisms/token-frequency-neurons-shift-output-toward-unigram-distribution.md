---
aliases:
- Token Frequency Neurons Shift Output Toward Unigram Distribution
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:token-frequency-neurons-shift-output-toward-unigram-distribution
  type: mechanism
  status: canonical
cause: A token frequency neuron boosts or suppresses each token's logit in proportion to that token's log corpus frequency
effect: The model's output distribution moves toward (or away from) the empirical unigram token-frequency distribution, changing its KL divergence from that distribution and its entropy
polarity: increases
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[token-frequency-neurons]]'
- '[[the-pile]]'
- '[[kl-divergence]]'
relationships:
- type: supported_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[token-frequency-neurons]]'
  target_id: term:token-frequency-neurons
  confidence: high
- type: related_to
  target: '[[the-pile]]'
  target_id: dataset:the-pile
  confidence: medium
- type: related_to
  target: '[[kl-divergence]]'
  target_id: metric:kl-divergence
  confidence: high
---

In Pythia 410M, Stolfo et al. identify neurons whose output weights correlate
with each token's log frequency in The Pile. Output entropy is negatively
correlated with KL(P_freq || P_model), and ablating these neurons substantially
changes that divergence relative to a token-frequency-direction-held-constant
baseline, showing the neurons causally push the model's predictions toward or
away from the corpus-level unigram distribution.
