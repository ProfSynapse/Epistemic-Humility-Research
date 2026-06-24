---
aliases:
- SE label advantage for OOD
- semantic supervision beats accuracy supervision OOD
- intrinsic probing target generalizes better
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:se-supervision-improves-ood-probe-generalization
  type: mechanism
  status: canonical
cause: "Training a hidden-state probe with semantic entropy labels instead of ground-truth accuracy labels"
effect: "The probe generalizes better to held-out tasks, gaining 7.7-10.5 AUROC points on short-form models and 2.2-6.2 points on large long-form models relative to accuracy probes, while performing similarly in-distribution"
polarity: increases
related:
- '[[2406.15927--semantic-entropy-probes]]'
- '[[semantic-entropy-probes]]'
- '[[semantic-entropy]]'
- '[[p-ik-ood-generalization-gap]]'
- '[[verbalized-prob-generalizes-logit-overfits-distribution-shift]]'
- '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
relationships:
- type: supported_by
  target: '[[2406.15927--semantic-entropy-probes]]'
  target_id: paper:2406.15927
  confidence: high
- type: related_to
  target: '[[semantic-entropy-probes]]'
  target_id: method:semantic-entropy-probes
  confidence: high
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: high
- type: related_to
  target: '[[p-ik-ood-generalization-gap]]'
  target_id: mechanism:p-ik-ood-generalization-gap
  confidence: high
- type: related_to
  target: '[[verbalized-prob-generalizes-logit-overfits-distribution-shift]]'
  target_id: mechanism:verbalized-prob-generalizes-logit-overfits-distribution-shift
  confidence: high
- type: related_to
  target: '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
  target_id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  confidence: high
---

Accuracy probes are supervised with external correctness labels that may latch onto task-specific discriminative features (e.g., knowledge domains correlated with accuracy in the training tasks). SE is a more intrinsic model property, encoding the model's own distributional uncertainty over semantic meanings regardless of the ground-truth answer. This makes SE-supervised probes more portable across task distributions. The in-distribution gap is small (-2.0 to +2.8 points), but the OOD advantage is consistent and substantial across all six model-setting pairs tested, supporting the hypothesis that intrinsic uncertainty targets generalize better than extrinsic correctness targets.
