---
aliases:
- CFG
- unconditional guidance
- Classifier-Free Guidance
tags:
- kg/method
- concept
- method
kg:
  id: method:classifier-free-guidance
  type: method
  status: canonical
area: generative-models
related:
- '[[stable-diffusion]]'
- '[[score-representation]]'
relationships:
- type: related_to
  target: '[[stable-diffusion]]'
  target_id: model:stable-diffusion
- type: related_to
  target: '[[score-representation]]'
  target_id: method:score-representation
---

Classifier-Free Guidance (CFG) is an inference-time technique for conditional diffusion models that interpolates between a conditional score estimate and an unconditional score estimate: s_guided = s_uncond + w * (s_cond - s_uncond), where w controls guidance strength. Instead of requiring a separately trained classifier, a single network produces both estimates by conditioning on a null token during training. The difference (s_cond - s_uncond) forms a direction in activation space that [[score-representation|concept algebra]] exploits to compose semantic attributes across generative models. Higher values of w enforce stronger prompt adherence at the cost of reduced diversity.

**Why it matters here:** CFG demonstrates that meaningful semantic directions can be extracted from score differences inside a generative model, a structural analog to the linear probing of internal representations studied in epistemic-humility mechanistic work on [[linear-representation-hypothesis|linear representations]].

**Lineage:** no direct derivation from prior atoms; related to [[stable-diffusion]] (the principal deployment context) and [[score-representation]] (the score-difference object it produces and that concept algebra recombines).
