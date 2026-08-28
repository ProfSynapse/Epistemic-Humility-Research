---
aliases:
- Learned boundaries localize compact causal-variable subspaces
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:learned-subspace-boundaries-localize-compact-causal-variables
  type: mechanism
  status: canonical
cause: "Boundless DAS jointly optimizes representation rotation and annealed soft boundaries for aligned variables."
effect: "Successful runs isolate each tested causal variable in a small fraction of the representation space while preserving intervention accuracy."
polarity: enables
related:
- '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
- '[[boundless-distributed-alignment-search]]'
relationships:
- type: supported_by
  target: '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
  target_id: paper:2305.08809
  confidence: high
- type: related_to
  target: '[[boundless-distributed-alignment-search]]'
  target_id: method:boundless-distributed-alignment-search
  confidence: high
---

In successful runs, each causal variable used about 5% to 10% of the representation space. The authors report that IIA stayed stable as the learned boundaries shrank.
