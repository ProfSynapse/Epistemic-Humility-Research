---
aliases:
- latent stitching
tags:
- kg/method
- concept
- method
kg:
  id: method:sae-stitching
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2502.04878--sparse-autoencoders-do-not-find-canonical-units]]'
- '[[sparse-autoencoder]]'
- '[[novel-latent]]'
- '[[reconstruction-latent]]'
- '[[feature-splitting]]'
- '[[canonical-units-of-analysis]]'
relationships:
- type: proposed_by
  target: '[[2502.04878--sparse-autoencoders-do-not-find-canonical-units]]'
  target_id: paper:2502.04878
  confidence: high
- type: derived_from
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

A method for comparing SAEs of different dictionary sizes by systematically
adding or swapping clusters of latents between SAEs based on decoder cosine
similarity. Larger-SAE latents are classified as novel (cosine similarity below
a 0.7 threshold, indicating genuinely new representational content) or
reconstruction (cosine similarity at or above 0.7, indicating redundant
refinements of smaller-SAE features), and the effect of adding each cluster on
reconstruction MSE is measured to assess completeness and atomicity. This
classification underpins the [[novel-latent]] and [[reconstruction-latent]]
distinction used in [[feature-splitting]] analysis.

**Why it matters here:** Stitching reveals whether increased dictionary size
yields genuinely new representational capacity or mere refinement, which matters
for deciding how large an SAE must be to expose all causally relevant features,
including latent epistemic signals such as uncertainty or answerability.

**Lineage:** derives from [[sparse-autoencoder]] comparison methodology;
introduced alongside the [[canonical-units-of-analysis]] analysis in the
2502.04878 paper.
