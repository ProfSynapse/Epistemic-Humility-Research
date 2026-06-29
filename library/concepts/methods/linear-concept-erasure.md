---
aliases:
- Linear Concept Erasure
- LEACE
- concept erasure
tags:
- kg/method
- concept
- method
kg:
  id: method:linear-concept-erasure
  type: method
  status: canonical
area: methods
related:
- '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
- '[[answerability-subspace]]'
- '[[linear-probe]]'
relationships:
- type: proposed_by
  target: '[[2310.11877--curious-case-hallucinatory-un-answerability-finding-truths]]'
  target_id: paper:2310.11877
  confidence: medium
- type: related_to
  target: '[[answerability-subspace]]'
  target_id: term:answerability-subspace
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Linear concept erasure (LEACE) is a closed-form affine transformation of a
representation that provably removes all linearly-decodable information about a
target concept while minimally perturbing the representation otherwise. Applied
to a hidden state, it makes any linear probe for the erased concept perform at
chance, so it serves as a causal test of whether a behavior depends on the
linearly-encoded concept.

**Why it matters here:** It is the causal-intervention complement to a linear
probe: erasing the answerability subspace and observing that the model's
answerability behavior degrades shows the linear direction is functionally used,
not merely correlated. This is the methodology for moving an answerability axis
from "decodable" to "causally implicated."

**Lineage:** Belrose et al. 2023 (LEACE); used by Slobodkin et al. 2023 to ablate
the [[answerability-subspace]] read by a [[linear-probe]].
