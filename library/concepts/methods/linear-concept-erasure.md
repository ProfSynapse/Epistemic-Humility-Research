---
aliases:
- Linear Concept Erasure
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
- '[[inlp]]'
- '[[rlace]]'
- '[[leace]]'
relationships:
- type: related_to
  target: '[[answerability-subspace]]'
  target_id: term:answerability-subspace
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[inlp]]'
  target_id: method:inlp
  confidence: high
- type: related_to
  target: '[[rlace]]'
  target_id: method:rlace
  confidence: high
- type: related_to
  target: '[[leace]]'
  target_id: method:leace
  confidence: high
---

Linear concept erasure is the family of methods that transform a representation
so that no linear predictor can recover a target concept from it, while
perturbing the representation as little as possible. Members include [[inlp]]
(iterative nullspace projection), [[rlace]] (rank-constrained adversarial
erasure), and [[leace]] (closed-form, provably minimal-distortion erasure).
Applied to a hidden state, erasure makes any linear probe for the concept
perform at chance, so it serves as a causal test of whether a behavior depends
on the linearly-encoded concept (the amnesic-probing paradigm).

**Why it matters here:** It is the causal-intervention complement to a linear
probe: erasing the answerability subspace and observing that the model's
answerability behavior degrades shows the linear direction is functionally used,
not merely correlated. This is the methodology for moving an answerability axis
from "decodable" to "causally implicated."

**Lineage:** INLP (Ravfogel et al. 2020) introduced iterative guarding; RLACE
(Ravfogel et al. 2022) reduced it to a minimal rank-k subspace; LEACE (Belrose
et al. 2023) gave the closed-form optimum. Used by Slobodkin et al. 2023 to
ablate the [[answerability-subspace]] read by a [[linear-probe]].
