---
aliases:
- BBH
- BIG-Bench Hard
- BIG-Bench Hard (BBH)
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:big-bench-hard
  type: dataset
  status: canonical
area: benchmarks
related: []
relationships: []
---

BIG-Bench Hard is a curated subset of 23 tasks drawn from the BIG-Bench benchmark suite, selected specifically because state-of-the-art models performed substantially worse than average human raters on these tasks at the time of curation. The tasks span logical deduction, causal reasoning, commonsense understanding, natural language inference, and algorithmic problem solving. It serves as a standard hard-difficulty evaluation surface that separates models capable of genuine multi-step reasoning from those relying on shallow pattern matching.

**Why it matters here:** BBH tasks tend to require explicit reasoning chains, making the benchmark a natural testbed for studying whether chain-of-thought prompting improves calibration and whether verbalized confidence on hard tasks tracks actual accuracy.

**Lineage:** no prior atom dependency; a curated difficulty-filtered descendant of BIG-Bench.
