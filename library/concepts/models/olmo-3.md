---
aliases:
- OLMo-3-1025-7B
- OLMo-3-7B
- OLMo-3
tags:
- kg/model
- concept
- model
kg:
  id: model:olmo-3
  type: model
  status: canonical
area: training-dynamics
related: []
relationships: []
---

OLMo-3 is an open-weights base language model at 7B parameters released by the Allen Institute for AI, notable for providing publicly available intermediate pretraining checkpoints spanning the full training trajectory. It also ships post-trained instruct variants (SFT, DPO, and RLVR), making it possible to study representation formation from pretraining through each alignment stage on a single model family.

**Why it matters here:** The availability of dense early checkpoints enables [[pretraining-checkpoint-tracing]] directly on this model, supporting the claim that epistemic representations such as persona-like axes emerge during pretraining rather than being installed by post-training alignment.

**Lineage:** no direct derivation; primary model family studied in work on persona-vector tracing.
