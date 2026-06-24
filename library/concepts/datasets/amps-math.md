---
aliases:
- AMPS Math
- AMPS Mathematica dataset
- no-steps algebra AMPS
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:amps-math
  type: dataset
  status: canonical
area: datasets
related:
- '[[2502.08177--syceval]]'
- '[[medquad]]'
- '[[sycophancy]]'
- '[[progressive-regressive-sycophancy-taxonomy]]'
relationships:
- type: proposed_by
  target: '[[2502.08177--syceval]]'
  target_id: paper:2502.08177
  confidence: high
- type: related_to
  target: '[[medquad]]'
  target_id: dataset:medquad
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[progressive-regressive-sycophancy-taxonomy]]'
  target_id: term:progressive-regressive-sycophancy-taxonomy
  confidence: medium
---

A large collection of mathematics question-answer pairs generated from manually designed Mathematica scripts, covering algebra subcategories including conic sections, polynomial GCD, De Moivre's theorem, and function inverses. SycEval samples 500 pairs from the no-steps algebra subset for sycophancy evaluation.

**Why it matters here:** Provides a structured computational domain where answers are objectively verifiable, making it a clean testbed for regressive vs progressive sycophancy. Its objective nature produces domain-specific effects absent in open-ended datasets: preemptive rebuttals drive significantly more regressive sycophancy on AMPS than on MedQuad.

**Lineage:** Introduced by Hendrycks et al. (2021) as part of the MATH benchmark infrastructure; used in SycEval (2502.08177) as the mathematics evaluation split.
