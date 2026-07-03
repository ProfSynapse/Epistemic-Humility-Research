---
aliases:
- LoRA merging with DARE
- model merging for multi-behavior
tags:
- kg/method
- concept
- method
kg:
  id: method:lora-dare
  type: method
  status: canonical
area: methods
related: []
relationships: []
---

Multi-behavior steering approach that trains separate behavior-specific low-rank
adapter (LoRA) modules and then merges them using the DARE interference-reduction
technique (Yu et al. 2024). Operates in parameter space rather than activation or
input-embedding space. Achieves competitive performance on seen behavior combinations
but fails to generalize compositionally to unseen behavior pairs, making it a useful
upper-bound baseline for in-distribution behavior coverage.

**Why it matters here:** As a parameter-space alternative to [[activation-steering]]
and [[compositional-steering-tokens]], LoRA-DARE establishes that parameter merging
alone does not yield the compositional generalization needed to flexibly combine
epistemic behaviors (such as calibrated abstention) with task-specific skills across
new configurations at inference time.

**Lineage:** builds on [[low-rank-adaptation]] modules with DARE-style delta-weight
sparsification for interference reduction; compared against [[activation-steering]]
and [[compositional-steering-tokens]] in the multi-behavior steering evaluation.
