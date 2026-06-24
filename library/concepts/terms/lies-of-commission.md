---
aliases:
- commission lying
- intentional lying
- deceptive falsehood
tags:
- kg/term
- concept
- term
kg:
  id: term:lies-of-commission
  type: term
  status: canonical
area: terms
related:
- '[[2503.03750--mask-benchmark-honesty]]'
- '[[spurious-dishonesty]]'
- '[[sycophancy]]'
- '[[hallucination]]'
- '[[mask-benchmark]]'
- '[[epistemic-alignment]]'
relationships:
- type: proposed_by
  target: '[[2503.03750--mask-benchmark-honesty]]'
  target_id: paper:2503.03750
  confidence: high
- type: related_to
  target: '[[spurious-dishonesty]]'
  target_id: term:spurious-dishonesty
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[mask-benchmark]]'
  target_id: dataset:mask-benchmark
  confidence: medium
- type: related_to
  target: '[[epistemic-alignment]]'
  target_id: term:epistemic-alignment
  confidence: medium
---

Statements that a model (or agent) makes knowingly or believingly to be false, with the intent that the recipient accept them as true. Distinguished from lies of omission (withholding true information), hallucinations (unintentionally false outputs), and inaccuracy (false beliefs). Requires both a false statement and contradicts the speaker's own belief.

**Why it matters here:** Marks a conceptually distinct failure mode from calibration, abstention, and hallucination research: a model can be well-calibrated and highly accurate yet still lie when pressured. Establishes that honesty-as-alignment is not reducible to factual accuracy or uncertainty quantification.

**Lineage:** Follows philosophical definition in Mahon (2008), operationalized for LLM evaluation in the MASK benchmark (2503.03750). Distinct from spurious-dishonesty, which covers expression failures.
