---
aliases:
- TunedLens
- tuned lens probe
tags:
- kg/method
- concept
- method
kg:
  id: method:tuned-lens
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
- '[[logit-lens]]'
- '[[linear-probe]]'
- '[[prediction-trajectory]]'
- '[[representational-drift]]'
relationships:
- type: proposed_by
  target: '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
  target_id: paper:2303.08112
  confidence: high
- type: derived_from
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[prediction-trajectory]]'
  target_id: term:prediction-trajectory
- type: related_to
  target: '[[representational-drift]]'
  target_id: term:representational-drift
---

The tuned lens is a per-layer affine probe trained on a frozen pretrained
transformer that maps each intermediate hidden state to a probability
distribution over the vocabulary. For each layer l the method learns a
translator (A_l, b_l) that corrects for representational drift between
intermediate layers and the final unembedding direction, producing vocabulary
distributions that are more predictive of the final output than the raw logit
lens. The translators are fit by minimising cross-entropy against the model's
own final-layer predictions, requiring no external labels. This makes the tuned
lens applicable to models where the logit lens fails (such as BLOOM and OPT)
because those models use layernorm or embedding scaling that breaks the direct
readout assumption.

**Why it matters here:** The tuned lens produces per-layer prediction
trajectories that can be used to study whether uncertainty or self-knowledge
signals develop gradually or appear abruptly at a particular depth, which is
directly relevant to mechanistic probing for epistemic-humility-related
representations.

**Lineage:** extends [[logit-lens]] by adding a learnable affine correction per
layer; introduced by [[2303.08112--tuned-lens-eliciting-latent-predictions]];
addresses [[representational-drift]] and produces [[prediction-trajectory]]
sequences.
