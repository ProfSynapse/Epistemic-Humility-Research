---
aliases:
- Anomalous prediction trajectory signatures detect prompt injection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:prediction-trajectory-detects-prompt-injection
  type: mechanism
  status: canonical
cause: Prompt injection attacks alter the model's layer-by-layer prediction trajectory in a detectable way relative to normal prompts
effect: An anomaly detector trained on tuned lens prediction trajectories achieves near-perfect AUROC on five of seven tasks (BoolQ, MNLI, QNLI, QQP, SST-2) for detecting prompt injection attacks
polarity: enables
related:
- '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
- '[[prediction-trajectory]]'
- '[[tuned-lens]]'
- '[[tuned-lens-affine-correction-restores-fidelity]]'
relationships:
- type: supported_by
  target: '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
  target_id: paper:2303.08112
  confidence: high
- type: related_to
  target: '[[prediction-trajectory]]'
  target_id: term:prediction-trajectory
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
- type: related_to
  target: '[[tuned-lens-affine-correction-restores-fidelity]]'
  target_id: mechanism:tuned-lens-affine-correction-restores-fidelity
---

Because prompt injection fundamentally redirects the model's internal computation, it leaves a distinctive signature in the layer-by-layer [[prediction-trajectory]] produced by the [[tuned-lens]]: the trajectory diverges from normal-prompt patterns in ways that a lightweight anomaly detector can learn to recognize (arXiv:2303.08112). A detector trained on tuned lens trajectories achieves near-perfect AUROC on five of seven GLUE-style classification tasks (BoolQ, MNLI, QNLI, QQP, SST-2) for identifying injected prompts. This detection capability is enabled specifically by the causal fidelity of the tuned lens; the logit lens, lacking affine correction, does not provide sufficiently reliable trajectory signals for the same purpose.
