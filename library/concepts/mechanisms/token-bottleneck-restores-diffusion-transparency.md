---
aliases:
- Interpretable Token Bottleneck Reduces DiffusionGemma Opaque Serial Depth
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:token-bottleneck-restores-diffusion-transparency
  type: mechanism
  status: canonical
cause: Mapping information between DiffusionGemma denoising steps through an interpretable token bottleneck
effect: The model's effective opaque serial depth drops from much larger than Gemma 4 to approximately comparable with Gemma 4
polarity: enables
related:
- '[[2606.20560--how-transparent-is-diffusiongemma]]'
- '[[diffusiongemma]]'
- '[[opaque-serial-depth]]'
- '[[reasoning-transparency]]'
relationships:
- type: supported_by
  target: '[[2606.20560--how-transparent-is-diffusiongemma]]'
  target_id: paper:2606.20560
  confidence: high
- type: related_to
  target: '[[diffusiongemma]]'
  target_id: model:diffusiongemma
- type: related_to
  target: '[[opaque-serial-depth]]'
  target_id: metric:opaque-serial-depth
- type: related_to
  target: '[[reasoning-transparency]]'
  target_id: term:reasoning-transparency
---

Engels et al. report that DiffusionGemma appears to have 28.6x the empirical
opaque serial depth upper bound of the corresponding Gemma 4 model if its
intermediate denoising bottleneck is treated as uninterpretable. When the
intermediate token bottleneck is treated as interpretable, the ratio falls to
1.1x.

**Why it matters here:** This mechanism makes the transparency question
architectural and diagnostic rather than binary: preserving inspectable
intermediate bottlenecks may keep latent or diffusion reasoning auditable.
