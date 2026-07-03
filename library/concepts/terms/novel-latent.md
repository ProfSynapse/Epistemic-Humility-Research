---
aliases:
- novel feature
tags:
- kg/term
- concept
- term
kg:
  id: term:novel-latent
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2502.04878--sparse-autoencoders-do-not-find-canonical-units]]'
- '[[feature-splitting]]'
relationships:
- type: proposed_by
  target: '[[2502.04878--sparse-autoencoders-do-not-find-canonical-units]]'
  target_id: paper:2502.04878
  confidence: high
- type: related_to
  target: '[[feature-splitting]]'
  target_id: term:feature-splitting
---

A latent in a larger SAE that has low cosine similarity to every latent in a smaller SAE trained on the same activations (below 0.7 in GPT-2 experiments, below 0.4 in Gemma Scope), indicating it captures information absent from the smaller dictionary. Adding novel latents from a 1536-feature GPT-2 SAE to a 768-feature SAE reduces reconstruction MSE by roughly 10 percent, providing direct evidence that smaller SAEs are incomplete rather than merely coarser versions of larger ones.

**Why it matters here:** If SAE latents encoding doubt or caution signals are novel latents relative to smaller dictionaries, probes trained on under-sized SAEs will systematically miss them, producing false negatives in epistemic-humility interpretability studies.

**Lineage:** related to [[feature-splitting]], which describes how individual latents subdivide into more specific sub-features as dictionary size grows; novel latent emergence is the complementary phenomenon where entirely new directions appear.
