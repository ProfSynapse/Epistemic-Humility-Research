---
aliases:
- The evidence-maximizing direction reconstructs retrieval-family geometry, not doubt
- d_ev orders refused above confab above correct, the opposite of a doubt axis
- Asymmetric evidence-direction transfer to the KUQ population
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:evidence-contrast-direction-encodes-answer-availability-not-doubt
  type: mechanism
  status: canonical
cause: "In evidence-response-direction-search (M4c), the same d_ev direction (already shown to fail the covariance-shaped specificity null) is read on the auxiliary refused-role rows of its own test population and on the doubt-snap KUQ population's anchor states via a mirror-direction transfer readout, with the KUQ-fit c_hat direction transferred back onto d_ev's own rows as the reverse comparator."
effect: "On its own population, d_ev orders refused (AUROC vs correct 0.9751) above confab (0.7252) above correct, the opposite ordering a doubt axis should show (a doubt axis should place refusals and confident wrongness on the same side, against confident correctness). Transfer is also asymmetric: d_ev separates confab-vs-correct on the KUQ population at AUROC 0.7762 (CI [0.7360, 0.8156]), while the KUQ-fit c_hat direction fails to transfer back onto d_ev's own rows in reverse (AUROC 0.2845 on the same rows). Both facts point the same way: d_ev tracks whether an answer is available or retrievable at all, a property of the model's retrieval success, not whether the model doubts a specific committed answer. The evidence contrast, when maximized, reconstructs retrieval-family/answer-availability geometry rather than a doubt axis."
polarity: complicates
related:
- '[[evidence-response-direction-search]]'
- '[[evidence-fit-direction-recovers-no-specific-doubt-axis]]'
- '[[kuq-fit-direction-reverses-on-world-known-confident-wrongness]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[known-unknown-direction]]'
relationships:
- type: supported_by
  target: '[[evidence-response-direction-search]]'
  target_id: experiment:evidence-response-direction-search
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md#outcome (Ungated readouts; FINDING construct tell)
- type: related_to
  target: '[[evidence-fit-direction-recovers-no-specific-doubt-axis]]'
  target_id: mechanism:evidence-fit-direction-recovers-no-specific-doubt-axis
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md (same direction, same cell; this mechanism diagnoses what the direction actually encodes)
- type: related_to
  target: '[[kuq-fit-direction-reverses-on-world-known-confident-wrongness]]'
  target_id: mechanism:kuq-fit-direction-reverses-on-world-known-confident-wrongness
  confidence: medium
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md#outcome (KUQ transfer readout; asymmetric transfer footnote)
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: medium
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md (KUQ transfer readout uses doubt-snap's anchor extraction)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
---

A doubt axis, by the margin-theory framework's own construct, should place
refusals and confident wrongness on the same side, opposite confident
correctness: both refusing and confabulating are failures to commit to a
correct answer, distinct from actually knowing one. `d_ev` instead orders
refused above confab above correct, the signature of a direction that tracks
whether the model can retrieve an answer at all rather than one that tracks
self-directed doubt about a specific answer it has committed to.

The transfer asymmetry corroborates the same reading independently. `d_ev`,
fit purely on PopQA world-known evidence, generalizes to the disjoint KUQ
population at a real AUROC (0.7762), while the KUQ-fit direction fails to
generalize back onto `d_ev`'s own rows in reverse (0.2845). A direction tied
to a specific evidence contrast would not be expected to transfer cleanly to
an unrelated population's answerability regime; a direction riding generic
retrieval-family geometry, which both PopQA and KUQ rows share regardless of
population, would. This mechanism is a diagnostic complement to
[[evidence-fit-direction-recovers-no-specific-doubt-axis]]: that mechanism
establishes that `d_ev` is not specific to the evidence contrast it was fit
on; this one identifies what it is riding instead. Source of truth:
`experiments/evidence-response-direction-search/AMENDMENT.md` (Outcome,
Ungated readouts and FINDING sections).
