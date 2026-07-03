---
aliases:
- SAE model diffing
- activation diffing
- Model-Diffing with SAEs
tags:
- kg/method
- concept
- method
kg:
  id: method:model-diffing
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2506.19823--persona-features-control-emergent-misalignment]]'
- '[[sparse-autoencoder]]'
- '[[activation-steering]]'
- '[[misaligned-persona-feature]]'
relationships:
- type: proposed_by
  target: '[[2506.19823--persona-features-control-emergent-misalignment]]'
  target_id: paper:2506.19823
  confidence: high
- type: derived_from
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: variation_of
  target: '[[activation-steering]]'
  target_id: method:activation-steering
---

Model diffing is a four-step interpretability procedure for identifying which SAE latents change between a base model and a fine-tuned variant. Step 1 collects SAE latent activations on a fixed evaluation prompt set for both checkpoints. Step 2 ranks latents by the largest activation increase after fine-tuning. Step 3 verifies causality by steering each top latent bidirectionally and measuring its effect on a target behavioral metric (e.g., [[misalignment-score]]), subject to an incoherence constraint: responses rated incoherent on more than 10% of prompts disqualify the candidate latent. Step 4 interprets causally relevant latents by inspecting their top-activating pre-training documents to assign a human-readable concept label.

**Why it matters here:** Model diffing provides a principled path from observed behavioral change to mechanistic cause, enabling researchers to identify which internal representations mediate alignment shifts rather than treating fine-tuning effects as opaque black-box changes.

**Lineage:** derives from [[sparse-autoencoder]] (the representational layer it operates on); is a variant of [[activation-steering]] (steering latents to verify causal relevance); proposed in [[2506.19823--persona-features-control-emergent-misalignment]].
