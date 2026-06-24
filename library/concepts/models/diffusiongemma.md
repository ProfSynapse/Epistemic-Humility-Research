---
aliases:
- DiffusionGemma
- DiffusionGemma 26B A4B
tags:
- kg/model
- concept
- model
kg:
  id: model:diffusiongemma
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[2606.20560--how-transparent-is-diffusiongemma]]'
- '[[gemma-4]]'
- '[[text-diffusion-language-model]]'
relationships:
- type: studied_by
  target: '[[2606.20560--how-transparent-is-diffusiongemma]]'
  target_id: paper:2606.20560
  confidence: high
- type: derived_from
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: high
- type: related_to
  target: '[[text-diffusion-language-model]]'
  target_id: term:text-diffusion-language-model
---

DiffusionGemma is a text-diffusion reasoning model studied as a variant of
Gemma 4. Rather than generating strictly left to right, it refines a canvas
through denoising steps, allowing token predictions across the canvas to change
between steps.

**Why it matters here:** DiffusionGemma is a concrete test case for whether
latent or semi-latent reasoning architectures preserve chain-of-thought
transparency, monitorability, and uncertainty visibility.

**Lineage:** analyzed in [[2606.20560--how-transparent-is-diffusiongemma]] as a
diffusion counterpart to [[gemma-4]].
