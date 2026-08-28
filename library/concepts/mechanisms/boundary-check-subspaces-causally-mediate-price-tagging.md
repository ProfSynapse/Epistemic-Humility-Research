---
aliases:
- Alpaca price tagging is mediated by boundary-check subspaces
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:boundary-check-subspaces-causally-mediate-price-tagging
  type: mechanism
  status: canonical
cause: "Distributed interventions replace compact subspaces aligned with lower-bound and upper-bound boolean checks in Alpaca-7B."
effect: "The model's price-tagging output changes in agreement with the corresponding high-level boundary-check algorithm."
polarity: mediates
related:
- '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
- '[[boundless-distributed-alignment-search]]'
- '[[alpaca-7b]]'
relationships:
- type: supported_by
  target: '[[2305.08809--interpretability-scale-identifying-causal-mechanisms-alpaca]]'
  target_id: paper:2305.08809
  confidence: high
- type: related_to
  target: '[[boundless-distributed-alignment-search]]'
  target_id: method:boundless-distributed-alignment-search
  confidence: high
- type: related_to
  target: '[[alpaca-7b]]'
  target_id: model:alpaca-7b
  confidence: high
---

The boundary-check models reached maximum IIA of 0.90 and 0.86, while the two alternative algorithms peaked at 0.70 and 0.72. This supports the boundary-check account for this task and model, not a general account of numerical reasoning.
