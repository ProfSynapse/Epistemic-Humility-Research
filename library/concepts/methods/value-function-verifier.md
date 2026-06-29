---
aliases:
- Token-level value-function verifier
- per-token correctness value function
- token-level verifier
tags:
- kg/method
- concept
- method
kg:
  id: method:value-function-verifier
  type: method
  status: canonical
area: methods
related:
- '[[2110.14168--training-verifiers-solve-math-word-problems]]'
- '[[solution-verifier]]'
relationships:
- type: proposed_by
  target: '[[2110.14168--training-verifiers-solve-math-word-problems]]'
  target_id: paper:2110.14168
  confidence: high
- type: related_to
  target: '[[solution-verifier]]'
  target_id: method:solution-verifier
  confidence: high
---

A token-level value-function verifier emits a scalar correctness prediction after
every solution token rather than a single solution-level score: a per-token value
function over the partial solution. It is the default verifier configuration in
Cobbe et al. 2021 and renders the verifier as an interpretable per-token
confidence trajectory that exposes where in a generation a correctness signal
becomes reliable.

**Why it matters here:** It is the finer-grained ancestor of process/step-level
reward models and is directly relevant to the token-position question for a
confidence/correctness head: at which token does a readout of correctness become
trustworthy. It also shows per-token correctness supervision resists overfitting
relative to a single end-of-sequence score.

**Lineage:** Cobbe et al. 2021 (Section 4.3); a finer-grained variant of the
[[solution-verifier]]; precursor to process reward models.
