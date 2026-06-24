---
aliases:
- compound mean faithful generation score
- cMFG*
- faithful calibration compound metric
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:cmfg-star
  type: metric
  status: canonical
area: metrics
related:
- '[[2606.03969--faithful-calibration-framework]]'
- '[[linguistic-decisiveness-scorer]]'
- '[[prefix-conditioned-sampling]]'
- '[[faithful-calibration]]'
- '[[verbalized-confidence]]'
- '[[consistency-based-confidence]]'
- '[[generation-discrimination-gap]]'
relationships:
- type: proposed_by
  target: '[[2606.03969--faithful-calibration-framework]]'
  target_id: paper:2606.03969
  confidence: high
- type: related_to
  target: '[[linguistic-decisiveness-scorer]]'
  target_id: method:linguistic-decisiveness-scorer
  confidence: medium
- type: related_to
  target: '[[prefix-conditioned-sampling]]'
  target_id: method:prefix-conditioned-sampling
  confidence: medium
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
---

A scalar metric that multiplies a model's linguistic decisiveness score by its estimator-specific intrinsic confidence score to yield a single faithful calibration value. Computed separately for each of three estimators (RCC, DeepConf, Sampling Consistency), yielding cMFG*_R, cMFG*_D, and cMFG*_S. Higher values indicate that verbal expression of confidence tracks internal uncertainty more closely.

**Why it matters here:** Provides a composable handle on faithful calibration that can expose whether a training intervention affects verbal behavior, internal confidence, or both, rather than collapsing the two into a single score that masks decoupling.

**Lineage:** Introduced in Gani et al. 2026 (arXiv:2606.03969) as part of their faithful calibration framework for large reasoning models.
