---
title: evidence-response-direction-search
aliases:
- 'M4c: evidence-derived doubt direction constructive search'
- evidence-derived doubt direction constructive search
tags:
- kg/experiment
- experiment
- doubt-snap
- margin-theory
kg:
  id: experiment:evidence-response-direction-search
  type: experiment
  status: canonical
related:
- '[[margin-evidence-responsiveness-worldknown]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[evidence-registration-exists-without-driving-behavior-worldknown]]'
- '[[evidence-fit-direction-recovers-no-specific-doubt-axis]]'
- '[[evidence-contrast-direction-encodes-answer-availability-not-doubt]]'
relationships:
- type: builds_on
  target: '[[margin-evidence-responsiveness-worldknown]]'
  target_id: experiment:margin-evidence-responsiveness-worldknown
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md (Motivation and posture; M4c inverts M4-WK's leg-2 pass into a constructive fit on the same evidence contrast)
- type: builds_on
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: medium
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md (KUQ transfer readout reuses doubt-snap's anchor extraction and fit_rows_for_anchor roles)
- type: related_to
  target: '[[evidence-registration-exists-without-driving-behavior-worldknown]]'
  target_id: mechanism:evidence-registration-exists-without-driving-behavior-worldknown
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md (Relation to prior cells; M4-WK leg-2 is the existence proof M4c's fit inverts)
- type: supports
  target: '[[evidence-fit-direction-recovers-no-specific-doubt-axis]]'
  target_id: mechanism:evidence-fit-direction-recovers-no-specific-doubt-axis
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md#outcome (Rung (c), D_c FAILS, all flavors)
- type: supports
  target: '[[evidence-contrast-direction-encodes-answer-availability-not-doubt]]'
  target_id: mechanism:evidence-contrast-direction-encodes-answer-availability-not-doubt
  confidence: high
  evidence:
  - experiments/evidence-response-direction-search/AMENDMENT.md#outcome (FINDING construct tell; Ungated readouts)
---

The margin-theory framework's earnability criterion (d) asks whether a named
direction "responds to evidence the way doubt should." `margin-evidence-responsiveness-worldknown`
(M4-WK) found the ingredient for this on its native direction: a real,
evidence-specific projection shift (leg 2 pass) that was nonetheless too small
along that direction to collapse the projection (leg 1 fail), a result read
as fragmentation (the evidence leg and the ignorance leg do not co-locate on
the native axis). M4c inverts the audition: instead of testing whether a
pre-fit ignorance direction responds to evidence, it fits a direction,
`d_ev`, to maximize the in-context true-vs-false evidence contrast itself
(the mean paired difference of `true_answer` minus `false_answer_placebo`
hs20 anchors over 200 fit confab rows) and asks whether that constructed
direction independently tracks prospective ignorance at baseline.

Resolved 2026-07-18 as a NULL-RESULT, qwen35_4b only, exploratory
instrument/mechanism tier, never pooled with the locked Phase 1 headline
matrix. `d_ev` fires at baseline (held-out confab-vs-correct AUROC 0.7252,
clearing the 0.70 floor) but fails specificity against covariance-shaped
random directions and every other null flavor tested, and is decisively
weaker than the native ignorance-fit direction on the identical rows
([[evidence-fit-direction-recovers-no-specific-doubt-axis]]). Diagnostic
readouts on the same direction show it orders refused above confab above
correct and transfers asymmetrically to the KUQ population, the signature of
retrieval-family/answer-availability geometry rather than doubt
([[evidence-contrast-direction-encodes-answer-availability-not-doubt]]). The
rung-(b) steering ladder was NOT RUN: its pre-registered funding condition (a
rung-(a) pass) was met, but the PI declined funding since the pass-a-fail-c
outcome cannot be changed by rung (b) under the signed outcome table. Post-run
red-team returned RESOLVE WITH DISCLOSURES (0 blockers, 0 majors, 2 minors,
all disclosed in the Outcome). M4-WK's fragmentation reading stands,
strengthened from "the pieces do not co-locate on the native axis" to "the
pieces do not co-locate on any linearly recoverable axis reachable from the
evidence contrast." Source of truth:
`experiments/evidence-response-direction-search/AMENDMENT.md`.
