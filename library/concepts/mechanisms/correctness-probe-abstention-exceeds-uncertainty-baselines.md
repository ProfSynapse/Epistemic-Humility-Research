---
aliases:
- Correctness Probe Abstention Exceeds Uncertainty Baselines
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:correctness-probe-abstention-exceeds-uncertainty-baselines
  type: mechanism
  status: canonical
cause: "Using a held-out linear correctness probe (layer 21) trained on the same decodable failure structure that fixed linear steering cannot exploit, as a post-generation abstention gate"
effect: "Higher selective-abstention discrimination (test AUROC=0.610) than every one of five tested single-forward-pass uncertainty baselines (best baseline AUROC=0.569, Delta AUROC=0.041, p=0.009), even though the probe direction cannot be used by steering for correction"
polarity: enables
related:
- '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[decodability-steerability-gap]]'
relationships:
- type: supported_by
  target: '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
  target_id: paper:2605.05715
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
- type: related_to
  target: '[[decodability-steerability-gap]]'
  target_id: term:decodability-steerability-gap
contradicted-by: []
---

[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]] shows that decodable failure structure remains useful even when it cannot be exploited for correction: a held-out linear correctness probe at layer 21 gives selective abstention a test AUROC of 0.610, beating all five single-forward-pass uncertainty baselines tested (best baseline AUROC=0.569, Delta AUROC=0.041, p=0.009). This demonstrates that the same probe-derived structure the paper's steering interventions fail to exploit for correction can still be exploited for post-generation reliability estimation, separating the classification and correction uses of a decodable signal.
