---
aliases:
- hallucination taxonomy world model
- perceptual hallucination
- action-marginalized hallucination
- scene-diverging hallucination
tags:
- kg/term
- concept
- term
kg:
  id: term:world-model-hallucination-modes
  type: term
  status: canonical
area: verification
related:
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
relationships:
- type: proposed_by
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
---

A three-type taxonomy of failure modes in generative world models, each anchored to a different pipeline stage. Perceptual hallucination occurs when the tokenizer encoder-decoder projects out-of-distribution scenes onto in-distribution exemplars, producing corrupted reconstructions at horizon H=0. Action-marginalized hallucination arises when the dynamics model is insensitive to input actions, generating visually plausible but action-independent rollouts. Scene-diverging hallucination emerges when multi-step rollouts accumulate compounding error, producing physically implausible events in low-coverage state regions.

**Why it matters here:** Each mode corresponds to a distinct coverage failure in the training distribution, connecting world model reliability to the epistemic question of what a model does and does not know about its environment. The taxonomy enables targeted diagnostic and remediation strategies rather than treating hallucination as a monolithic failure.

**Lineage:** introduced by [[2606.27326--hallucination-world-models-predictable-preventable]].
