---
aliases:
- similar latent
- redundant latent
tags:
- kg/term
- concept
- term
kg:
  id: term:reconstruction-latent
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

A latent in a larger SAE that has high cosine similarity to a corresponding latent in a smaller SAE trained on the same activations (at least 0.7 in GPT-2 experiments), indicating both dictionaries represent the same feature at comparable fidelity. Approximately 94 percent of latents are reconstruction latents when comparing same-size SAEs of different random seeds, establishing within-size consistency as a strong baseline and distinguishing seed noise from genuine size-dependent variation.

**Why it matters here:** The high prevalence of reconstruction latents shows SAE training is stable for well-represented features, supporting the view that epistemic-signal probes can be reliably replicated across seeds when the underlying signal is strong enough.

**Lineage:** related to [[feature-splitting]], the process by which reconstruction latents subdivide into more specific sub-features as dictionary size grows; contrasts with [[novel-latent]], which captures entirely new directions.
