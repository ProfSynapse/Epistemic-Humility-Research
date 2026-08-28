---
aliases:
- OPCD
- On-Policy Context Distillation
tags:
- kg/method
- concept
- method
kg:
  id: method:on-policy-context-distillation
  type: method
  status: canonical
area: methods
related:
- '[[2602.12275--policy-context-distillation-language-models]]'
- '[[context-distillation]]'
- '[[on-policy-distillation]]'
relationships:
- type: proposed_by
  target: '[[2602.12275--policy-context-distillation-language-models]]'
  target_id: paper:2602.12275
  confidence: high
- type: derived_from
  target: '[[context-distillation]]'
  target_id: method:context-distillation
  confidence: high
- type: derived_from
  target: '[[on-policy-distillation]]'
  target_id: method:on-policy-distillation
  confidence: high
---

On-Policy Context Distillation samples complete trajectories from a
context-free student, then minimizes token-level reverse KL divergence to a
teacher that receives the target context. The training objective transfers
information from prompts or accumulated experience into the student's weights.

**Why it matters here:** OPCD is an explicit method for making a model produce
context-conditioned behavior without supplying that context at inference time.

**Lineage:** It combines [[context-distillation]] with
[[on-policy-distillation]].
