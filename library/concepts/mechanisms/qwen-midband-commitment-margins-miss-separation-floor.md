---
title: qwen-midband-commitment-margins-miss-separation-floor
aliases:
- margins are real and correctly placed but the separation criterion narrowly fails
- observable ratio bound 2.0 vs registered floor 2.5 (qwen mid-band)
- margin-theory Claim 1 falsified at the qwen mid-band operating point
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen-midband-commitment-margins-miss-separation-floor
  type: mechanism
  status: canonical
cause: "In the margin-mapping experiment (M1), per-row commitment margins (the minimum ladder dose along the frozen Qwen3.5-4B hs20 c_hat direction, reference dose_abs 12.608, that flips a row to well-formed abstention) were measured for 400 confab rows and the full 360-row known pool via a 10-rung geometric ladder (0.0625x-4x reference dose), against the pre-registered censoring-aware separation criterion: (a) median confab margin at or below the family setpoint, and (b) the observable ratio (highest pre-collapse rung divided by median confab margin) at or above a 2.5 floor."
effect: "Both supporting checks pass: the setpoint 12.608 lies between the confab median (9.456 dose_abs) and the known censored region above the highest pre-collapse rung, and 70.0% of known rows (Wilson 95% CI [0.651, 0.745]) neither tipped nor collapsed there, satisfying leg (a) and the censoring clause of leg (b). But the observable ratio itself is exactly 18.912 / 9.456 = 2.0, short of the 2.5 floor (bootstrap 95% CI [2.0, 3.0], a rung-quantized statistic). Framework Claim 1 (per-row commitment margins separate confab from known rows by at least the registered floor) is falsified at the qwen mid-band operating point as registered, even though the margin distributions retrodict the gate-contribution factorial's permuted-gate and baseline anchor rates within the 0.10 tolerance (max error 0.083) and construct-integrity checks pass (detector-vs-adjudication disagreement 0.029 vs a 0.05 ceiling; non-monotone fractions 0.035 confab / 0.011 known, both within ceiling). A red-teamed derivation-time arithmetic error in the floor-derivation prose (a one-rung numerator mismatch) meant the floor was expected to be narrowly clearable (2.52); the realized confab median landed one ladder rung above the fitted pre-run expectation (9.456 vs 7.506), and the registered criterion does not move for that reason."
polarity: complicates
related:
- '[[margin-mapping]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[commitment-margin]]'
- '[[gate-contribution-factorial]]'
- '[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]'
- '[[qwen35-4b-midband-doubt-snap]]'
relationships:
- type: supported_by
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md#outcome (Criterion verdicts P1
    separation, P2 setpoint placement, P3 retrodiction, C1 construct integrity)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 1)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Design, Per-row deliverables;
    tipping dose is the operationalized commitment margin)
- type: related_to
  target: '[[gate-contribution-factorial]]'
  target_id: experiment:gate-contribution-factorial
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md#outcome (P3 retrodiction; permuted_confab
    predicted 0.618 vs observed 0.693, permuted_known 0.063 vs 0.065)
- type: related_to
  target: '[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]'
  target_id: mechanism:doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift
  confidence: medium
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Design, Retrodiction targets; the
    permuted-gate anchor rates retrodicted here are that mechanism's own
    fired-conditional rates)
- type: related_to
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: medium
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Design, Retrodiction targets; the
    doubt-snap dose-8 known anchor is excluded as in-sample per registration)
---

The margin-mapping experiment gives margin theory's Claim 1 its first direct
per-row test, and the result splits: the commitment margin construct itself
is validated (setpoint correctly placed between the two margin populations,
the measured distributions independently retrodict a prior registered
result within tolerance, and the readout survives its own integrity checks),
but the specific pre-registered separation floor is missed by exactly one
ladder rung's worth of margin. The observable-bound criterion was reformulated
censoring-aware precisely because the fitted known-margin median sits far
past the collapse boundary in the coherent-output regime (fitted median
229.7 dose_abs vs a collapse boundary near 25 dose_abs), so a raw median
ratio was never observable; even under that more conservative, rung-quantized
statistic, the bound lands at the lowest value the ladder could produce short
of clearing the floor.

**Why it matters here:** this is the first falsification inside the
margin-theory cascade
(`docs/research/margin-theory-framework.md`, section 4), and it falsifies
narrowly and at a single operating point, not categorically. The floor itself
carried a one-rung numerator error at derivation time (it used the
collapse-boundary dose rather than the highest pre-collapse rung), so the
pre-run expectation was 2.52 against the 2.5 floor; the realized value came
in one rung below that already-tight margin. Both registered predictors
called qwen separation PASS and were wrong, while both were right on
placement, retrodiction, and the qualitative H4 overdrive slot. The
mistral7b_v03 leg of this experiment is VOID_INSTRUMENT_LOSS (hs16 direction
destroyed in the 2026-07-17 worktree-sweep incident), so whether this
narrow miss is a Qwen-specific or general finding is unresolved; see
[[boundary-anisotropy]] for the family-level property this would otherwise
have helped measure.

**Lineage:** first empirical test of Claim 1 in
[[margin-theory-of-epistemic-state]], introduced 2026-07-16 in
`docs/research/margin-theory-framework.md`. Reuses the frozen mid-band
operating point and retrodicts the fired-conditional anchor rates from
[[gate-contribution-factorial]]'s
[[doubt-gate-adds-sub-floor-selectivity-write-drives-abstention-lift]]
result. Source of truth: `experiments/margin-mapping/AMENDMENT.md`, Outcome
section, resolved 2026-07-17.
