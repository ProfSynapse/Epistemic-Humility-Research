---
aliases:
- dataset diversity unlocks cross-task probe generalization
- diversity-not-volume drives probe OOD accuracy
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:diverse-training-enables-universal-probe-generalization
  type: mechanism
  status: canonical
cause: "Training a linear truthfulness probe on a large collection of diverse datasets spanning many task types and domains"
effect: "Cross-task and cross-domain probe accuracy improves substantially (roughly 14 points over single-dataset baselines), while per-dataset sample volume has negligible impact (10 samples per dataset matches 800)"
polarity: enables
related:
- '[[2407.08582--generalizable-truth-probes]]'
- '[[universal-truthfulness-hyperplane]]'
- '[[universal-truthfulness-probe]]'
- '[[p-ik-ood-generalization-gap]]'
- '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
- '[[pretrained-latent-representations-enable-calibration-generalization]]'
relationships:
- type: supported_by
  target: '[[2407.08582--generalizable-truth-probes]]'
  target_id: paper:2407.08582
  confidence: high
- type: related_to
  target: '[[universal-truthfulness-hyperplane]]'
  target_id: term:universal-truthfulness-hyperplane
  confidence: high
- type: related_to
  target: '[[universal-truthfulness-probe]]'
  target_id: method:universal-truthfulness-probe
  confidence: high
- type: related_to
  target: '[[p-ik-ood-generalization-gap]]'
  target_id: mechanism:p-ik-ood-generalization-gap
  confidence: high
- type: related_to
  target: '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
  target_id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  confidence: high
- type: related_to
  target: '[[pretrained-latent-representations-enable-calibration-generalization]]'
  target_id: mechanism:pretrained-latent-representations-enable-calibration-generalization
  confidence: high
---

Liu et al. find that the key bottleneck for OOD truthfulness probing is task diversity, not data volume. A probe trained on 49 datasets across 17 task categories achieves approximately 70% cross-task accuracy on LLaMA2-7b-chat, versus near-chance for a probe trained on TruthfulQA alone. The improvement transfers to Mistral-7b (77.11%) and LLaMA2-13b-chat (73.88%). Crucially, matching 800 samples per dataset requires only 10 samples per dataset, consistent with the linear probe's low sample complexity. The mechanism is interpreted as learning a more universal truthfulness direction rather than a distribution-specific spurious feature.
