---
aliases:
- A token-level value-function verifier resists overfitting
- per-token correctness supervision resists overfitting
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:value-function-verifier-resists-overfitting
  type: mechanism
  status: canonical
cause: "Training the verifier as a per-token value function (correctness prediction after every solution token) rather than a single solution-level scalar."
effect: "Less overfitting and a higher final test solve rate; a joint language-modeling objective adds a further strict improvement."
polarity: increases
related:
- '[[2110.14168--training-verifiers-solve-math-word-problems]]'
- '[[value-function-verifier]]'
- '[[solution-verifier]]'
relationships:
- type: supported_by
  target: '[[2110.14168--training-verifiers-solve-math-word-problems]]'
  target_id: paper:2110.14168
  confidence: high
- type: related_to
  target: '[[value-function-verifier]]'
  target_id: method:value-function-verifier
  confidence: high
- type: related_to
  target: '[[solution-verifier]]'
  target_id: method:solution-verifier
  confidence: medium
---

Cobbe et al. 2021 find per-token value-function verifiers train slower at first
but keep improving and ultimately beat solution-level verifiers, which overfit
early; the per-token signal judges reasoning throughout the solution rather than
memorizing the final answer, and adding a joint LM objective is a strict further
improvement (Section 4.3).
