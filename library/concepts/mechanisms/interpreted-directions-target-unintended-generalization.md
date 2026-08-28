---
aliases:
- Interpreted directions target unintended generalization
- Concept interpretation selects useful CAFT directions
- Selected latent concepts outperform random ablation controls
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:interpreted-directions-target-unintended-generalization
  type: mechanism
  status: canonical
cause: "Human or automated interpretation selects principal components or sparse-autoencoder latents linked to an undesired behavior."
effect: "Ablating those directions during fine-tuning suppresses the targeted generalization more than random or magnitude-only controls."
polarity: explains
related:
- '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
- '[[concept-ablation-finetuning]]'
- '[[sparse-autoencoder]]'
relationships:
- type: supported_by
  target: '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
  target_id: paper:2507.16795
  confidence: medium
- type: related_to
  target: '[[concept-ablation-finetuning]]'
  target_id: method:concept-ablation-finetuning
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
  confidence: high
---

The paper reports that interpreted PCA directions and SAE latents often
outperform random, largest-difference, or top-activation baselines. This
supports the narrower mechanism that semantic selection contributes to CAFT's
effect beyond applying an arbitrary low-rank perturbation.

The result is not universal. PCA and SAE variants differ by model and task,
and several synthetic tasks show weak or mixed effects.
