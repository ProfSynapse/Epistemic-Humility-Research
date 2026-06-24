---
aliases:
- calibratable regime
- non-calibratable regime
- calibration regime partition
- accuracy-calibration regime
tags:
- kg/term
- concept
- term
kg:
  id: term:calibratable-non-calibratable-regime
  type: term
  status: canonical
area: terms
related:
- '[[2505.01997--restoring-calibration-aligned-llms]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
- '[[calibration-aware-fine-tuning]]'
- '[[regularized-calibration-aware-fine-tuning]]'
relationships:
- type: proposed_by
  target: '[[2505.01997--restoring-calibration-aligned-llms]]'
  target_id: paper:2505.01997
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[calibration-aware-fine-tuning]]'
  target_id: method:calibration-aware-fine-tuning
  confidence: medium
- type: related_to
  target: '[[regularized-calibration-aware-fine-tuning]]'
  target_id: method:regularized-calibration-aware-fine-tuning
  confidence: medium
---

A theoretical partition of the accuracy-ECE space derived from upper and lower bounds on ECE as a function of model accuracy relative to a target probabilistic generative model. In the calibratable regime (model accuracy below the critical accuracy threshold), ECE can be driven to zero without sacrificing accuracy. In the non-calibratable regime (accuracy above the threshold), a strictly positive ECE lower bound holds, making perfect calibration structurally impossible under the target distribution.

**Why it matters here:** The regime partition determines which recalibration strategy is appropriate: CFT for calibratable models, RCFT for non-calibratable ones. It also formalises why temperature scaling fails as a general solution: it does not move the model along the accuracy dimension and therefore cannot cross the regime boundary.

**Lineage:** Proposed in arXiv:2505.01997, Section 4.2. Builds on the Target Calibration Error (TCE) framework introduced in the same paper.
