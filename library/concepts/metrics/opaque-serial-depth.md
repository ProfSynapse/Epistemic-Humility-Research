---
aliases:
- opaque serial depth
- OSD
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:opaque-serial-depth
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[2606.20560--how-transparent-is-diffusiongemma]]'
- '[[reasoning-transparency]]'
- '[[text-diffusion-language-model]]'
relationships:
- type: measured_by
  target: '[[2606.20560--how-transparent-is-diffusiongemma]]'
  target_id: paper:2606.20560
  confidence: high
- type: related_to
  target: '[[reasoning-transparency]]'
  target_id: term:reasoning-transparency
- type: related_to
  target: '[[text-diffusion-language-model]]'
  target_id: term:text-diffusion-language-model
---

Opaque serial depth is the amount of serial computation a model can perform
without passing through an interpretable state or bottleneck.

**Why it matters here:** Opaque serial depth quantifies a core risk of latent
reasoning: as more computation happens away from interpretable text, a model
may become harder to monitor even if its final answer remains fluent.
