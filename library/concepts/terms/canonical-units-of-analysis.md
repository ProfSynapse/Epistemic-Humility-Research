---
aliases:
- canonical features
- atomic features
- canonical feature set
tags:
- kg/term
- concept
- term
kg:
  id: term:canonical-units-of-analysis
  type: term
  status: canonical
area: mechanistic-interpretability
related: []
relationships: []
---

The hypothetical unique, complete, and irreducible set of features that sparse autoencoders were postulated to converge on given sufficient dictionary size. The hypothesis predicted that SAEs of different sizes trained on the same activations would eventually agree on a single set of atomic concepts. Empirically, smaller SAEs are incomplete (they miss novel latents that larger SAEs find) and larger SAEs are non-atomic (their latents decompose into combinations of smaller-SAE features), so no canonical set has been identified.

**Why it matters here:** If a canonical feature set existed, uncertainty and epistemic-humility signals could be precisely localized to stable, size-invariant features; the absence of such a set means interpretability findings about caution or doubt axes may shift with dictionary size.

**Lineage:** a foundational assumption in the early SAE literature, now empirically contested; see [[novel-latent]] and [[reconstruction-latent]] for the evidence that motivated revising it.
