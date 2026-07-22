---
title: margin-mapping
aliases:
- 'Margin mapping: per-row tipping dose along the known-unknown direction'
- M1 margin-mapping
- per-row commitment margin staircase
tags:
- kg/experiment
- experiment
- cross-family
- margin-theory
kg:
  id: experiment:margin-mapping
  type: experiment
  status: canonical
related:
- '[[gate-contribution-factorial]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[ungated-vs-gated-dose-matched]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[commitment-margin]]'
- '[[boundary-anisotropy]]'
- '[[qwen-midband-commitment-margins-miss-separation-floor]]'
relationships:
- type: builds_on
  target: '[[gate-contribution-factorial]]'
  target_id: experiment:gate-contribution-factorial
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Design; substrate, direction, and
    populations reused byte-identical from the factorial staging; retrodiction
    targets include the factorial permuted-gate and baseline arms)
- type: builds_on
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Design, Retrodiction targets; the
    doubt-snap hs20 permuted-gate row-level dose ladder anchors the threshold
    derivation and is a retrodiction target flagged in-sample)
- type: related_to
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: medium
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Design, Retrodiction targets; the
    H4 overdrive anchor is retrodicted qualitatively only, from the collapse
    boundary's existence rather than deep-overdrive rungs)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Prediction and Falsifier; framework
    Claim 1 and Claim 2, the keystone of the margin-theory cascade)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md (Design, Per-row deliverables;
    tipping dose and collapse dose definitions)
- type: related_to
  target: '[[boundary-anisotropy]]'
  target_id: term:boundary-anisotropy
  confidence: low
  evidence:
  - experiments/margin-mapping/AMENDMENT.md#outcome (mistral7b_v03 VOID_INSTRUMENT_LOSS
    leaves the cross-family anisotropy comparison untested by this experiment)
- type: supports
  target: '[[qwen-midband-commitment-margins-miss-separation-floor]]'
  target_id: mechanism:qwen-midband-commitment-margins-miss-separation-floor
  confidence: high
  evidence:
  - experiments/margin-mapping/AMENDMENT.md#outcome (Criterion verdicts P1-C1;
    Margin distributions)
---

Registered per-row dose staircase along the frozen known-unknown direction
(`c_hat`) at the mid-band operating points reused byte-identically from the
gate-contribution factorial: Qwen3.5-4B hs20 (reference dose_abs 12.608) and
Mistral-7B-Instruct-v0.3 hs16 (reference dose_abs 3.665). This is experiment
M1, the keystone of the margin-theory cascade
(`docs/research/margin-theory-framework.md`, section 4): the first
measurement of per-row commitment margins, the minimum dose that flips a row
to well-formed abstention, for the existing confab and known pools in both
families. A 10-rung geometric ladder (0.0625x-4x reference dose) was scored
by a detector-v2 primary readout with a registered blinded-adjudication
calibration slice, against a pre-registered censoring-aware separation
criterion, a setpoint-placement criterion, a three-anchor retrodiction test,
and a construct-integrity gate (non-monotone ceiling plus the calibration
disagreement floor).

Resolved 2026-07-17, qwen35_4b only. Mistral7b_v03 is VOID_INSTRUMENT_LOSS:
its hs16 direction vector was destroyed in the 2026-07-17 worktree-sweep
incident, reconstruction failed the pre-registered byte-identity acceptance
rule (bf16 forward-pass non-determinism, no capture-convention discrepancy
found by forensics), and the PI directed the qwen-only fallback before any
mistral staircase data existed. All mistral criterion and scoreboard slots
are unscored; the loss is incident-driven, not results-driven, and the
cross-family anisotropy comparison this experiment was designed to feed is
untested here.

On qwen35_4b, the mid-band commitment margins are mechanistically real and
correctly placed: the setpoint 12.608 sits between the confab median (9.456
dose_abs) and the known censored region (P2 pass); the margin distributions
retrodict the factorial permuted-gate and baseline anchor rates within the
0.10 tolerance, max error 0.083 (P3 pass); and construct integrity holds,
detector-vs-adjudication disagreement 0.029 against a 0.05 ceiling and both
non-monotone fractions within their ceilings (C1 pass). The registered
primary criterion nonetheless fails: the observable ratio bound (highest
pre-collapse rung 18.912 dose_abs over median confab margin 9.456) is exactly
2.0, short of the pre-registered floor of 2.5 (bootstrap 95% CI [2.0, 3.0]).
Framework Claim 1 (per-row commitment margins separate confab from known
rows by at least the registered floor) is falsified at the qwen mid-band
operating point as registered, detailed in
[[qwen-midband-commitment-margins-miss-separation-floor]]. Both registered
predictors called qwen separation PASS and were wrong; the differentiating
mistral scoreboard slots are void, so no predictor is declared correct. No
locked verdict moves: this is exploratory instrument/mechanism-tier evidence,
reported separately from the Phase 1 headline matrix. Source of truth:
`experiments/margin-mapping/AMENDMENT.md`.
