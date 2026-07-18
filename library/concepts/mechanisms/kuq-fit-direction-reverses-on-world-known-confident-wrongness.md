---
aliases:
- KUQ doubt direction reverses on confident-wrong-on-answerable rows
- The named doubt direction reads unanswerability, not self-directed uncertainty
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:kuq-fit-direction-reverses-on-world-known-confident-wrongness
  type: mechanism
  status: canonical
cause: "In margin-evidence-responsiveness-worldknown (M4-WK), the KUQ-fit c_hat direction (fit on answered-vs-refused known-unknown rows, the direction the framework's earnability criteria previously licensed the name 'doubt' for on that population) is projected, unmodified, onto a disjoint world-known population: PopQA rows split into confident-wrong-on-answerable (confab, n=400) and correct-on-answerable (control, n=360), under the same negative-z convention used on its own KUQ fit."
effect: "The direction does not transfer: baseline confab-vs-correct AUROC on the world-known population is 0.3018 (bootstrap 95% CI [0.2647, 0.3396]), far below the pre-registered 0.70 firing floor, while an independent reproduction confirms the same direction still reads its own KUQ population at AUROC 0.9867 under the identical harness convention, ruling out a sign-flip artifact. The raw projections genuinely reverse in sign between populations: KUQ confab (answered-on-unknown) rows are more negative than correct rows, but world-known confab (confident-wrong-on-answerable) rows are more POSITIVE than correct rows. The direction's reading is closer to unanswerability recognition (a property of the question) than to self-directed uncertainty about one's own answer (a property of the answer): it fires on not-knowing-that-one-doesn't-know, not on being wrong while answering."
polarity: complicates
related:
- '[[margin-evidence-responsiveness-worldknown]]'
- '[[known-unknown-direction]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[margin-evidence-responsiveness-worldknown]]'
  target_id: experiment:margin-evidence-responsiveness-worldknown
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (Transfer direction (primary))
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: medium
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md (Motivation and posture; the direction under test is fit there)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: medium
- type: related_to
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: medium
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (unanswerability recognition vs self-directed uncertainty)
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

The margin-theory framework's earnability criterion (d) asks whether a named
direction "responds to evidence the way doubt should." Before this cell, the
KUQ-fit c_hat already satisfied criteria (a)-(c) on its own known-unknown
population, which is why the framework's working prose called it "doubt."
M4-WK tests criterion (d) on a different error class the direction was never
fit on: confident-wrongness on answerable world-known questions.

The direction does not merely fail to fire weakly; it reverses. On its native
KUQ population, confab (answered-on-unknown) rows read more negative than
correct rows. On the world-known population, confident-wrong-on-answerable
rows read more POSITIVE than correct rows, the opposite sign relationship. An
independent adversarial reproduction, run specifically to rule out a harness
sign-flip before this was accepted, confirmed the direction's own-population
AUROC reproduces at 0.9867 under the exact same projection convention (a real
sign-flip artifact would have produced 0.0133, not 0.3018), so the reversal is
a property of the direction's fit, not a bug in this cell's harness.

Per the framework's own falsifier logic, a non-firing transfer voids
criterion (d) on this population rather than falsifying evidence-
responsiveness outright: the population is out of the direction's domain.
What the reversal does establish is a positive alternative reading. The KUQ
fit contrasts answered-on-unknown rows against refused-on-unknown rows; both
row types are equally unanswerable, so the only systematic difference the
fit could have latched onto is not the ANSWER's correctness but a residual
correlate of the question itself, or of whether the model recognized it as
unanswerable at all. That is closer to unanswerability recognition, a
question-property signal, than to self-directed uncertainty about a given
answer, which is what the mentalistic name "doubt" implies. Source of truth:
`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md` (Outcome,
Transfer direction section).
