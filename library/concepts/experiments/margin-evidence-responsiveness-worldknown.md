---
title: margin-evidence-responsiveness-worldknown
aliases:
- 'Evidence-responsiveness on world-known QA: the M4 rebase (M4-WK)'
- World-known confident-wrongness naming test for the KUQ doubt direction
tags:
- kg/experiment
- experiment
- doubt-snap
- margin-theory
kg:
  id: experiment:margin-evidence-responsiveness-worldknown
  type: experiment
  status: canonical
related:
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[margin-mapping]]'
- '[[kuq-fit-direction-reverses-on-world-known-confident-wrongness]]'
- '[[confident-wrongness-steering-hits-coherence-ceiling-before-refusal]]'
- '[[evidence-registration-exists-without-driving-behavior-worldknown]]'
relationships:
- type: builds_on
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md (Design; the transfer direction is reused byte-identically from this experiment's committed c_hat)
- type: builds_on
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: medium
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md (Design; margin/ladder schema and reusable-artifact conventions carried from M1)
- type: supports
  target: '[[kuq-fit-direction-reverses-on-world-known-confident-wrongness]]'
  target_id: mechanism:kuq-fit-direction-reverses-on-world-known-confident-wrongness
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (Transfer direction (primary))
- type: supports
  target: '[[confident-wrongness-steering-hits-coherence-ceiling-before-refusal]]'
  target_id: mechanism:confident-wrongness-steering-hits-coherence-ceiling-before-refusal
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (Native direction, FINDING saturation / coherence ceiling)
- type: supports
  target: '[[evidence-registration-exists-without-driving-behavior-worldknown]]'
  target_id: mechanism:evidence-registration-exists-without-driving-behavior-worldknown
  confidence: high
  evidence:
  - experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md#outcome (Native direction, D1 leg-1/leg-2, Channel 2 void)
---

Registered rebase of the void-by-design `margin-evidence-responsiveness`
(M4), which could not run because its KUQ-subsample population carries no
gold-answer field for the true-answer injection arm it requires. M4-WK moves
the same test, the framework's earnability criterion (d) ("responds to
evidence the way doubt should"), onto PopQA, a world-known population where
every row has a gold answer, redefining "confab" as
confident-wrong-on-answerable rather than answered-a-KUQ-unknown. Two
directions are tested: the KUQ-fit c_hat reused byte-identically from
`qwen35-4b-midband-doubt-snap` (TRANSFER, primary, the literal test of the
named direction), and a fresh world-known refit on a disjoint split (NATIVE,
secondary dissociation reading). Two channels probe each direction: a
projection-collapse channel (does supplying the true answer in-context move
the projection toward the correct/refused regime, specifically more than a
category-matched false-answer placebo) and a margin-lengthening channel
(does the true answer let the row survive its own tipping dose longer than
the placebo).

Resolved 2026-07-18 as a NULL-RESULT, qwen35_4b only, exploratory
instrument/mechanism tier, never pooled with the locked Phase 1 headline
matrix. The primary criterion (d) test is VOID rather than failed: the
transfer direction does not fire on the world-known population at all
(baseline AUROC 0.3018 against a 0.70 firing floor), and an adversarial
reproduction confirms this is a genuine population reversal, not a harness
sign-flip artifact
([[kuq-fit-direction-reverses-on-world-known-confident-wrongness]]). The
secondary native direction does fire (AUROC 0.8628) but does not earn
criterion (d) either: its projection response is real and evidence-specific
but sub-floor
([[evidence-registration-exists-without-driving-behavior-worldknown]]), and
its margin channel is separately voided by a coherence ceiling that dose
extension cannot resolve
([[confident-wrongness-steering-hits-coherence-ceiling-before-refusal]]).
Post-run red-team returned RESOLVE WITH DISCLOSURES (0 blockers, 2 majors, 7
minors; one major fixed pre-merge, the rest disclosed in the Outcome).
Source of truth:
`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md`.
