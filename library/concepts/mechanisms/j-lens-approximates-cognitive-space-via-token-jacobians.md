---
aliases:
- J-lens approximates model working memory through token Jacobians
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:j-lens-approximates-cognitive-space-via-token-jacobians
  type: mechanism
  status: canonical
cause: "Intermediate variables in multi-step language-model computation are stored in reusable residual-stream concept directions, and some of those directions are aligned with future token logits"
effect: "averaged output-token Jacobians provide a useful but noisy approximation to the model's cognitive space, outperforming logit lens on future-token and intermediate-variable readout while missing non-tokenized or multi-token concepts"
polarity: enables
related:
- '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
- '[[cognitive-space]]'
- '[[jacobian-lens]]'
- '[[logit-lens]]'
- '[[linear-representation-hypothesis]]'
relationships:
- type: supported_by
  target: '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
  target_id: paper:tc-2026-workspace-commentary-nanda
  confidence: high
- type: related_to
  target: '[[cognitive-space]]'
  target_id: term:cognitive-space
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
  confidence: high
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
  confidence: medium
---

Nanda's first-principles account is that multi-step model computation needs intermediate variables, the residual stream is the cross-layer bottleneck where such variables can live, and reusable concept variables should settle into consistent directions. J-lens works when these concept directions are aligned enough with future token logits that an averaged Jacobian can expose them; it remains approximate because many real concepts are not single tokens and causal interventions can magnify lens noise.
