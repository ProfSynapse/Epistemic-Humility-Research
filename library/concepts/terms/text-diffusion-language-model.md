---
aliases:
- text diffusion model
- text diffusion language model
- diffusion language model
- latent reasoning architecture
tags:
- kg/term
- concept
- term
kg:
  id: term:text-diffusion-language-model
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2606.20560--how-transparent-is-diffusiongemma]]'
- '[[diffusiongemma]]'
- '[[reasoning-transparency]]'
relationships:
- type: studied_by
  target: '[[2606.20560--how-transparent-is-diffusiongemma]]'
  target_id: paper:2606.20560
  confidence: high
- type: related_to
  target: '[[diffusiongemma]]'
  target_id: model:diffusiongemma
- type: related_to
  target: '[[reasoning-transparency]]'
  target_id: term:reasoning-transparency
---

A text-diffusion language model generates text by iteratively denoising a token
canvas rather than committing to one next token at a time. This allows multiple
positions to be revised during inference and can support non-chronological
reasoning patterns.

**Why it matters here:** Text-diffusion language models create a new
monitorability question: a model may expose final natural-language reasoning
while also performing important computation in intermediate denoising states.
