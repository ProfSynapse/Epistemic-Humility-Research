---
aliases:
- SD
- latent diffusion model
tags:
- kg/model
- concept
- model
kg:
  id: model:stable-diffusion
  type: model
  status: canonical
area: generative-models
related:
- '[[classifier-free-guidance]]'
- '[[concept-algebra]]'
- '[[score-representation]]'
relationships:
- type: related_to
  target: '[[concept-algebra]]'
  target_id: method:concept-algebra
- type: related_to
  target: '[[score-representation]]'
  target_id: method:score-representation
---

Stable Diffusion is a large-scale text-to-image latent diffusion model that generates images by running an iterative denoising process in a compressed latent space rather than in pixel space, enabling high-quality synthesis at substantially reduced compute. The architecture pairs a pretrained VAE encoder-decoder for latent compression with a UNet backbone denoising score network conditioned on CLIP text embeddings via cross-attention. It serves as the primary empirical testbed for [[concept-algebra]] and [[score-representation]] because its [[classifier-free-guidance]] inference makes the centered score representation directly accessible.

**Why it matters here:** Not directly part of epistemic humility research; included as a reference anchor because [[concept-algebra]] and [[score-representation]] were introduced and validated on Stable Diffusion, and the geometric insights derived there inform analogous representation-editing approaches applied to language models in this research line.

**Lineage:** no lineage edges within this library; the model is a reference node for methods that originate in the score-based generative modeling literature.
