---
aliases:
- coverage gap
- data coverage gap
- low-coverage regions
- State-Action Coverage Gap
tags:
- kg/term
- concept
- term
kg:
  id: term:state-action-coverage-gap
  type: term
  status: canonical
area: verification
related: []
relationships: []
---

The condition in which a world model's training data has insufficient density in certain regions of the state-action space, causing the model to hallucinate when asked to generate predictions in those regions. Each of the three hallucination modes (perceptual, action-marginalized, scene-diverging) is interpreted as a coverage gap at a different pipeline stage: the tokenizer reconstruction distribution, the action-conditional transition distribution, and the multi-step rollout distribution. The central thesis is that all three failure modes are fundamentally data distribution problems rather than architectural limitations.

**Why it matters here:** Coverage gaps provide a mechanistic account of why generative models fail on out-of-distribution inputs, motivating interventions at the data level and connecting world model hallucination to the broader epistemic humility literature on knowledge boundaries.

**Lineage:** foundational term introduced as part of the hallucination-as-coverage-problem framing in [[2606.27326--hallucination-world-models-predictable-preventable]].
