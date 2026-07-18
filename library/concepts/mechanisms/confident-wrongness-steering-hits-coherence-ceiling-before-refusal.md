---
aliases:
- Steering confident-wrong-on-answerable rows hits a coherence ceiling
- Confident wrongness is harder to interrupt by steering than acknowledged ignorance
- The world-known margin ladder saturates at 12.75% tips, unresolvable by dose extension
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:confident-wrongness-steering-hits-coherence-ceiling-before-refusal
  type: mechanism
  status: canonical
cause: "In margin-evidence-responsiveness-worldknown (M4-WK), a world-known c_hat direction refit natively (baseline confab-vs-correct AUROC 0.8628) is applied at each row's own tipping dose along a rebuilt margin ladder (10 rungs, [0.0625, 4.0]x reference dose; PI-approved extension to [6.0, 8.0, 12.0, 16.0]x after a bracketing failure, repinned before any survival contrast) over 400 confident-wrong-on-answerable (confab) PopQA rows, with survival scored as non-abstaining and well-formed at each row's tipping dose."
effect: "Only 51/400 confab rows (12.75%) have a genuine, non-right-censored tipping dose at all; every one of those 51 tips at or below 2.0x the reference dose, and doses at or above 3.0x drive generation to 96-100% degenerate (non-well-formed) text before refusal ever registers. The PI-approved mid-run extension to 16x reference dose, pre-registered as a re-derivation option and repinned before any survival contrast was computed, added ZERO additional tips: the ceiling is unresolvable by further dose bracketing, not an artifact of an under-extended ladder. Contrast: the same steering family, on the direction's native KUQ population (answered-on-unknown rows), coherently tips roughly 77% of rows. Confident wrongness on an answerable question is mechanistically harder to interrupt along this steering axis than acknowledged ignorance is: the substrate runs out of room to represent 'refuse this' coherently long before the dose needed to move the remaining 87% of rows, collapsing into incoherent text instead."
polarity: prevents
related:
- '[[margin-evidence-responsiveness-worldknown]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[commitment-margin]]'
- '[[activation-steering]]'
- '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
- '[[qwen-midband-commitment-margins-miss-separation-floor]]'
relationships:
- type: supported_by
  target: '[[margin-evidence-responsiveness-worldknown]]'
  target_id: experiment:margin-evidence-responsiveness-worldknown
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (Native direction, FINDING saturation / coherence ceiling)
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: medium
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (Contrast: ~77% KUQ tip rate)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
  target_id: mechanism:steering-dose-windows-are-absolute-not-sigma-transferable
  confidence: medium
- type: related_to
  target: '[[qwen-midband-commitment-margins-miss-separation-floor]]'
  target_id: mechanism:qwen-midband-commitment-margins-miss-separation-floor
  confidence: medium
---

M1's margin ladder methodology (a per-row tipping dose, survival scored as
non-abstaining and well-formed) is rebuilt from scratch on a world-known
population because tipping doses do not transfer from the KUQ population the
ladder was originally built on. The rebuild surfaces a bracketing failure
distinct from anything in the KUQ lineage: 87.25% of confab rows sit
right-censored at the original 4.0x top rung, with no dose in range having
tipped them. Rather than silently treating right-censored rows as
non-tippable, the cell's registered bracketing-requirement clause escalates
to the PI, who approves extending the ladder to 16x reference dose before any
survival contrast is computed (preserving self-blinding).

The extension is diagnostic rather than merely exculpatory: it adds zero
tips. This rules out under-bracketing as the explanation and establishes the
ceiling as a property of the substrate, not the instrument. The per-rung
generation-health data pins down why: doses at or above 3.0x already drive
96-100% of generations to degenerate, non-well-formed text, so the model
loses the ability to produce a coherent refusal at exactly the doses that
would be needed to move the remaining rows. The 51 rows that do tip all do so
at or below 2.0x, the same narrow window the coherence collapse has not yet
reached.

The natural comparison is the direction's home population: on KUQ
(answered-on-unknown rows), the same steering family coherently tips roughly
77% of rows. World-known confident-wrongness is a harder target for this
steering axis to interrupt than acknowledged ignorance is, a mechanistic
asymmetry between the two error classes that the world-known rebase was
designed to be able to see (KUQ's confab rows carry no gold answer and so
could never have been split this way). Source of truth:
`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md` (Outcome,
Native direction section).
