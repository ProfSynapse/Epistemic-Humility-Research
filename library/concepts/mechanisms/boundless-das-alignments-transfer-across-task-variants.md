---
aliases:
- Boundless DAS causal alignments transfer across task variants
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:boundless-das-alignments-transfer-across-task-variants
  type: mechanism
  status: canonical
cause: "A Boundless DAS alignment captures a price-boundary variable rather than a fixed prompt or output string."
effect: "The alignment retains high interchange intervention accuracy under new brackets, irrelevant prefixes, and changed output labels."
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

Maximum IIA stayed between 0.83 and 0.95 across the paper's transfer settings. Correlations with the base alignment map remained between 0.87 and 0.99.
