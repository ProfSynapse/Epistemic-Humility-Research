---
title: gate-contribution-factorial
aliases:
- 'Gate-contribution factorial: does the doubt gate, not the write direction, produce selective abstention'
- 2x2 gate x direction factorial, qwen hs20 and mistral hs16
tags:
- kg/experiment
- experiment
- doubt-snap
- cross-family
kg:
  id: experiment:gate-contribution-factorial
  type: experiment
  status: canonical
related:
- '[[qwen35-4b-midband-heldout]]'
- '[[placebo-seed-distribution-census]]'
- '[[rr2-mistral-adjudicated-refusal-confirm]]'
- '[[doubt-gated-caution-tighten]]'
- '[[ungated-vs-gated-dose-matched]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]'
- '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
- '[[random-direction-placebo-response-is-family-specific-in-sign]]'
relationships:
- type: builds_on
  target: '[[qwen35-4b-midband-heldout]]'
  target_id: experiment:qwen35-4b-midband-heldout
  confidence: high
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md (Design, Families and frozen operating points; qwen baseline and true_gate__c_hat arms reused byte-identical)
- type: builds_on
  target: '[[placebo-seed-distribution-census]]'
  target_id: experiment:placebo-seed-distribution-census
  confidence: high
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md (Design, direction-specificity denominator; S1 uses the census K=15 max-over-K null)
- type: builds_on
  target: '[[rr2-mistral-adjudicated-refusal-confirm]]'
  target_id: experiment:rr2-mistral-adjudicated-refusal-confirm
  confidence: high
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md (Design, mistral frozen operating point; baseline and gated arm reused byte-identical)
- type: related_to
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: high
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md (Motivation and posture; tests that experiment's "selectivity comes from the gate, not the write" governing statement)
- type: related_to
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: medium
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md (Motivation and posture; contrasting operating point where the gate was the dominant discriminator)
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: medium
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md (Design, Permuted gate; construction follows that experiment's permuted-gate control)
- type: supports
  target: '[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]'
  target_id: mechanism:doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift
  confidence: high
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md#outcome (Verdict; Per-family criterion results)
- type: related_to
  target: '[[matched-magnitude-placebo-sign-survives-as-distributional-property]]'
  target_id: mechanism:matched-magnitude-placebo-sign-survives-as-distributional-property
  confidence: medium
  evidence:
  - experiments/gate-contribution-factorial/AMENDMENT.md#outcome (S1 direction-specificity evaluation)
- type: related_to
  target: '[[random-direction-placebo-response-is-family-specific-in-sign]]'
  target_id: mechanism:random-direction-placebo-response-is-family-specific-in-sign
  confidence: medium
---

Registered 2x2 factorial, {true doubt gate, fire-count-matched permuted gate}
x {true `c_hat` caution direction, K=5 fresh random directions} plus an
undosed baseline, scored on both the confab (unanswerable) and known-correct
(answerable) populations under the wide two-instrument stack. It resolves a
tension between three governed results none of which isolated the gate's own
contribution: `doubt-gated-caution-tighten`'s governing statement that "the
write itself is non-selective and all of the instrument's selectivity comes
from the gate, not the write"; the fact that statement was never tested under
the wide instrument or with a magnitude floor; and
`placebo-seed-distribution-census`'s finding that matched-magnitude random
directions are not behaviorally inert in any family, so a raw abstention-rate
delta cannot by itself certify what the gate contributes. Two families:
Qwen3.5-4B hs20 (dose_abs 12.608, the census operating point, primary) and
Mistral-7B-Instruct-v0.3 hs16 (dose_abs 3.665, RR2/RR3 lineage, secondary,
chosen because its direction axis is already falsified, making it the clean
dissociation case for the gate axis).

Resolved 2026-07-16, exploratory instrument/mechanism tier, reported
separately from every locked surface. The gate axis is falsified on both
families: the true doubt gate's selectivity-gap and cost-protection
contributions over a fire-count-matched permuted gate are both real (CIs
exclude zero) but sit entirely below their pre-registered floors
(`doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift`), so
the dosed write itself, not the gate's row selection, drives most of the
abstention behavior at these operating points. Direction-specificity (S1,
secondary, evaluated separately against the census K=15 null) dissociates by
family as designed: qwen passes by sign-opposition to the census suppressive
null (effect ratio 7.27), mistral fails as same-signed with the census
recruiting null (ratio 2.03), reproducing RR2/RR3's direction-axis failure
under a stricter denominator. All four integrity gate families (SC0-SC3)
passed, including recovery from a mid-run dose-squaring instrument defect
(SC1) that was caught pre-grading and fully remediated before any row was
unblinded; an adversarial red-team review returned CONFIRM-NULL for both
families. No locked verdict moves: the Phase 1 headline matrix, the census,
and the RR2/RR3/midband-heldout outcomes are untouched; what changes is the
interpretation available to the paper, since "gated dosing produces selective
abstention" can no longer be attributed to the gate's row selection at these
operating points. Source of truth:
`experiments/gate-contribution-factorial/AMENDMENT.md`.
