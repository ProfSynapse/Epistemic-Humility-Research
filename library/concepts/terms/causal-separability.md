---
aliases:
- concept causal separability
tags:
- kg/term
- concept
- term
kg:
  id: term:causal-separability
  type: term
  status: canonical
area: steering
related:
- '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
- '[[concept-algebra]]'
relationships:
- type: proposed_by
  target: '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
  target_id: paper:2302.03693
  confidence: high
---

Two concept variables Z and W are causally separable if varying Z does not affect the distribution over W in the data-generating process, and vice versa. The condition is the formal prerequisite for [[concept-algebra]] to edit one concept without perturbing the other: when concepts are correlated in training data (e.g., nationality and artistic style co-occur), the subspace projections overlap and editing bleeds across concept boundaries. Causal separability can be checked empirically by measuring interference after algebra is applied.

**Why it matters here:** The same entanglement problem arises for epistemic axes in language models: if uncertainty and helpfulness are coupled in RLHF training data, steering one will contaminate the other. Causal separability is therefore a prerequisite assumption when claiming that [[activation-steering]] on a confidence axis is clean.

**Lineage:** introduced in [[2302.03693--concept-algebra-score-based-text-controlled-generative]] as a validity condition for [[concept-algebra]]; related to [[representational-independence]] (independence between representation subspaces) and [[concept-orthogonality]].
