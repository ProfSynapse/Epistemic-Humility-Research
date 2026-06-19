---
aliases:
- causal tracing
- activation patching
tags:
- kg/method
- concept
- method
kg:
  id: method:activation-patching
  type: method
  status: canonical
area: methods
related:
- '[[2309.16042--towards-best-practices-of-activation-patching-in-language-models]]'
- '[[residual-stream-activation]]'
- '[[logit-difference]]'
relationships:
- type: proposed_by
  target: '[[2309.16042--towards-best-practices-of-activation-patching-in-language-models]]'
  target_id: paper:2309.16042
  confidence: medium
- type: applied_to
  target: '[[residual-stream-activation]]'
  target_id: term:residual-stream-activation
  confidence: high
- type: measures
  target: '[[logit-difference]]'
  target_id: metric:logit-difference
  confidence: medium
---

Activation patching replaces or perturbs internal activations to estimate
whether those activations causally contribute to a model output. This note also
uses the alias causal tracing for the same method family.

