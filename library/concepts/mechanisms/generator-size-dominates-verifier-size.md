---
aliases:
- Generator size matters more than verifier size
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:generator-size-dominates-verifier-size
  type: mechanism
  status: canonical
cause: "Independently scaling the generator versus the verifier model size in a sample-and-rank pipeline."
effect: "Solve rate improves more from a larger generator than from a larger verifier; verification stays effective even with a much smaller verifier."
polarity: increases
related:
- '[[2110.14168--training-verifiers-solve-math-word-problems]]'
- '[[solution-verifier]]'
- '[[best-of-n-sampling]]'
relationships:
- type: supported_by
  target: '[[2110.14168--training-verifiers-solve-math-word-problems]]'
  target_id: paper:2110.14168
  confidence: high
- type: related_to
  target: '[[solution-verifier]]'
  target_id: method:solution-verifier
  confidence: high
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: medium
---

Cobbe et al. 2021 find a large-generator / small-verifier pairing substantially
beats small-generator / large-verifier, and verification remains effective when
the verifier is much smaller than the generator, suggesting the verifier relies on
relatively coarse heuristics to discriminate among that generator's solutions
(Section 4.3).
