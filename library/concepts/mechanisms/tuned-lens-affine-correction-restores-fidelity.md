---
aliases:
- Learned affine correction in tuned lens restores causal fidelity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:tuned-lens-affine-correction-restores-fidelity
  type: mechanism
  status: canonical
cause: Training a per-layer affine translator (A_l, b_l) to minimize cross-entropy between the lens output and the final layer distribution
effect: Tuned lens features that are causally influential on the probe are also causally influential on the model itself (Spearman rho=0.89), and prediction trajectories are more predictive and less biased than the logit lens
polarity: increases
related:
- '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
- '[[tuned-lens]]'
- '[[logit-lens]]'
- '[[prediction-trajectory]]'
- '[[representational-drift-breaks-logit-lens]]'
relationships:
- type: supported_by
  target: '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
  target_id: paper:2303.08112
  confidence: high
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[prediction-trajectory]]'
  target_id: term:prediction-trajectory
- type: related_to
  target: '[[representational-drift-breaks-logit-lens]]'
  target_id: mechanism:representational-drift-breaks-logit-lens
---

The [[tuned-lens]] addresses [[representational-drift-breaks-logit-lens]] by learning a lightweight per-layer affine transformation (A_l, b_l) that maps each layer's hidden state into the final-layer representation space before applying the unembedding (arXiv:2303.08112). The affine correction is trained to minimize cross-entropy between lens output and the true final-layer distribution, aligning intermediate representations without distorting their causal structure: features that are causally influential on tuned-lens predictions are also causally influential on the model's actual output (Spearman rho=0.89). This causal alignment, absent in the logit lens, makes the tuned lens a reliable tool for constructing interpretable [[prediction-trajectory]] visualizations.
