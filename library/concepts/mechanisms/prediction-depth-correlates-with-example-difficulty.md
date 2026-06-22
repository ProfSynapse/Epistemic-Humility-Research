---
aliases:
- Prediction depth correlates with learning difficulty across training
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:prediction-depth-correlates-with-example-difficulty
  type: mechanism
  status: canonical
cause: Examples that require more training steps to learn also require more layers for the tuned lens to converge on a prediction
effect: Prediction depth (tuned lens) correlates with the training iteration at which examples are first answered correctly (Spearman rho up to 0.577), consistently outperforming logit lens depth
polarity: increases
related:
- '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
- '[[prediction-depth]]'
- '[[tuned-lens]]'
- '[[logit-lens]]'
relationships:
- type: supported_by
  target: '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
  target_id: paper:2303.08112
  confidence: high
- type: related_to
  target: '[[prediction-depth]]'
  target_id: metric:prediction-depth
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
---

[[prediction-depth]] -- the earliest layer at which the [[tuned-lens]] stably predicts the correct output -- serves as a proxy for example difficulty: harder examples require more layers before the model's internal representation settles on the correct prediction (arXiv:2303.08112). Correlating tuned lens prediction depth with the training checkpoint at which examples are first answered correctly yields Spearman rho up to 0.577, and this correlation consistently exceeds that obtained from logit lens depth on the same examples. The finding suggests that model computations are organized in a difficulty-hierarchical way that the tuned lens's affine correction makes legible.
