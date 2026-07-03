---
aliases:
- Steer2Adapt framework
- composed steering vector framework
- dynamic steering composition
tags:
- kg/method
- concept
- method
kg:
  id: method:steer2adapt
  type: method
  status: canonical
area: steering
related:
- '[[2602.07276--steer2adapt-dynamically-composing-steering-vectors-elicits-efficient]]'
- '[[activation-steering]]'
- '[[representation-engineering]]'
- '[[contrastive-activation-addition]]'
- '[[semantic-prior-subspace]]'
relationships:
- type: proposed_by
  target: '[[2602.07276--steer2adapt-dynamically-composing-steering-vectors-elicits-efficient]]'
  target_id: paper:2602.07276
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
- type: derived_from
  target: '[[representation-engineering]]'
  target_id: method:representation-engineering
- type: related_to
  target: '[[contrastive-activation-addition]]'
  target_id: method:contrastive-activation-addition
---

Steer2Adapt is a lightweight inference-time adaptation framework that composes existing semantic concept steering vectors to steer a language model toward new tasks using only a small number of labeled examples, without updating model parameters. Instead of searching over the full d-dimensional activation space, adaptation reduces to finding k coefficients (where k is much smaller than d) over a fixed [[semantic-prior-subspace]] spanned by pre-defined concept vectors, with the coefficients optimized via Bayesian optimization. This approach separates the expensive offline step of computing concept directions from the cheap online step of combining them, enabling efficient multi-behavior control at inference time.

**Why it matters here:** Steer2Adapt demonstrates that behavioral adaptation can be decomposed into a small number of semantic primitives, which directly bears on questions of epistemic humility: if refusal, hallucination, and sycophancy behaviors each have separable directions, then a single framework can simultaneously steer toward calibrated, honest, non-sycophantic outputs.

**Lineage:** extends [[activation-steering]] and is grounded in [[representation-engineering]]; related to [[contrastive-activation-addition]] as a specific contrastive method for producing the underlying concept vectors.
