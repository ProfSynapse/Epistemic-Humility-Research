---
title: 'Commitment-Point Stage 1: the Veto Is Already Saturated at the First Visible Token (Amendment AK, grpo-v2)'
tags:
- kg/paper
- paper
- epistemic-humility
- internal
kg:
  id: paper:internal-ak-commitment-point-stage1
  type: paper
  status: canonical
year: 2026
area: epistemic-humility
status: lab-notebook
source: internal
source_kind: epistemic-humility-research-program
authors:
- Joseph Rosenbaum (Synaptic Labs)
models:
- qwen3-4b
metrics:
- auroc
provenance: 'Internal amendment, Stage 1 (readout, no intervention). Amendment doc experiment/protocol/AMENDMENT-AK-commitment-point.md; Stage 1 analysis NOT yet merged to main, so provenance cites branch amendment-ak-commitment-point at analysis commit 069427dd. Committed record: experiment/phase1/probe/analysis-committed/ak_stage1_gate_verdicts.json plus ak_stage1_gate_verdicts.md; pilot floor analysis-committed/ak_stage1_pilot_floor.json (COMMITTED_FLOOR 5.291963, locked commit b6f560b8). Analysis script experiment/phase1/probe/amendment_ak_stage1_analyze.py (seed 20260705, deterministic). Data: raw-base config_sha 0dcb65d0062db64a, grpo-v2 config_sha 6394415378c83c96; 1,338 rows/arm (309 confab / 1,029 refuse), 50 pilot rows excluded from the AK-G2 test set. AK-G1 gates on grpo-v2; raw-base is descriptive. Exploratory lab-notebook evidence, never pooled with the locked headline matrix.'
related:
- '[[veto-saturates-by-first-visible-token]]'
- '[[post-generation-veto-is-rederived-not-carried]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[confabulation-propensity-direction]]'
- '[[internal-confab-mechanics--cpu-fleet]]'
- '[[known-unknown-direction]]'
- '[[linear-probe]]'
- '[[auroc]]'
- '[[unanswerable-questions]]'
relationships:
- type: supports
  target: '[[veto-saturates-by-first-visible-token]]'
  target_id: mechanism:veto-saturates-by-first-visible-token
  confidence: high
- type: related_to
  target: '[[post-generation-veto-is-rederived-not-carried]]'
  target_id: mechanism:post-generation-veto-is-rederived-not-carried
  confidence: high
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: studies
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: medium
- type: related_to
  target: '[[internal-confab-mechanics--cpu-fleet]]'
  target_id: paper:internal-confab-mechanics
  confidence: high
- type: studies
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: uses
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: studies
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: high
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

## Summary

Amendment AK Stage 1 traces the untested middle of the confabulation story: a
token-level generation-time readout on confab-vs-refuse generations, from the
prompt end through the first visible tokens to answer end, on both the raw
instruct base and the deployed clean-SFT to GRPO-v2 checkpoint. The pre-registered
question was whether the post-generation veto crystallizes across the answer
window and what the doubt-trunk reading does while a fabrication is being written.
On the gated grpo-v2 arm the veto does not crystallize: its readability is already
near-saturated at the first visible token (AUROC 0.9424) and drifts slightly down
to 0.9248 by answer-end, a delta of -0.0175 against a required +0.10, so AK-G1
misses. AK-G2 misses on the effect-size floor: the doubt-trajectory slope contrast
is real by permutation but too small in magnitude to adjudicate the three-way fork.
A descriptive direction split is unresolved between arms, so no doubt-trajectory
path is claimed. The full falsifier needs the Stage 2 steering leg (AK-G3, not
run), so it has not fired.

## Claims

- Evidence label: pre-registered crystallization gate (AK-G1, gated on grpo-v2).
  Veto AUROC at answer-end minus veto AUROC at first-visible token had to be at
  least +0.10; on grpo-v2 it is 0.9248 minus 0.9424 = -0.0175, so AK-G1 MISS. The
  veto is already assembled at the first visible token (0.94) and does not rise
  across the answer window. The random-direction guards read cleanly at
  0.486/0.529. (branch amendment-ak-commitment-point, analysis commit 069427dd;
  analysis-committed/ak_stage1_gate_verdicts.md; supports
  [[veto-saturates-by-first-visible-token]].)
- Evidence label: descriptive crystallization curve (raw-base, not the gate
  surface). The raw base rises across the window (+0.0341, from 0.9624 first-visible
  to 0.9966 answer-end) toward a near-perfect ceiling, but still far below the
  +0.10 bar. (same analysis commit.)
- Evidence label: pre-registered doubt-trajectory gate (AK-G2, three-way fork).
  PASS required the doubt-trunk slope contrast to clear the pilot-locked floor
  5.291963 AND permutation p below 0.01; grpo-v2 gives contrast -4.6234, CI
  [-5.382, -3.884], perm p = 1.0e-04, so the permutation leg passes but the
  magnitude leg fails (|contrast| 4.62 < floor 5.29). AK-G2 MISS-on-floor, an
  AJ-like on-the-line result where the CI contains the floor; no doubt-trajectory
  path is claimed. (same analysis commit; pilot floor committed b6f560b8.)
- Evidence label: descriptive direction split (NOT a claim). Confab-row doubt
  slopes point opposite ways between arms: grpo-v2 confab doubt RISES (+11.78,
  refuse +16.41, so the negative contrast reflects refuse rising faster) while
  raw-base confab doubt DROPS (-3.50, refuse +5.82). This grpo-v2-rise vs
  raw-base-drop divergence on the confab stratum is flagged as unadjudicated
  ambiguity. (same analysis commit.)
- Caveats: single model family (Qwen3-4B), single seed; Stage 1 is
  readout-not-causal, so only the Stage 2 steering leg (AK-G3, not run) could claim
  use. Per-position veto axes are refit out-of-fold with the AJ equal-rank
  random-direction guard. The falsifier (flat crystallization AND no steering
  asymmetry) needs Stage 2 and has not fired. Exploratory lab-notebook evidence,
  reported separately from and never pooled with the locked headline matrix.
</content>
