---
title: h6-genstream-hook-firing-check
aliases:
- Commitment-Point gen_stream Hook-Firing Check (H6)
- H6
tags:
- kg/experiment
- experiment
kg:
  id: experiment:h6-genstream-hook-firing-check
  type: experiment
  status: canonical
related:
- '[[unsloth-for-inference-decode-bypasses-steering-hook]]'
- '[[cross-trajectory-readback-fails-after-intervention-diverges]]'
- '[[activation-steering]]'
relationships:
- type: supports
  target: '[[unsloth-for-inference-decode-bypasses-steering-hook]]'
  target_id: mechanism:unsloth-for-inference-decode-bypasses-steering-hook
  confidence: high
  evidence:
  - experiments/h6-genstream-hook-firing-check/AMENDMENT.md#outcome
- type: supports
  target: '[[cross-trajectory-readback-fails-after-intervention-diverges]]'
  target_id: mechanism:cross-trajectory-readback-fails-after-intervention-diverges
  confidence: high
  evidence:
  - experiments/h6-genstream-hook-firing-check/AMENDMENT.md#outcome
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

Lab-diagnostic instrument check (paper 5 hardening item H6), not a
behavioral experiment: it decides whether either of two harness paths that
claim to steer during mid-generation (`gen_stream`, answer-window) decode
actually delivers a per-step write, replacing a smoke-flag assertion with an
on-vs-off readback. The gap it closes was diagnosed in the commitment-point
(AK) Stage 2 result, whose answer-window arm produced a signature (100%
byte-identical rows across seven steering doses) inconsistent with a
plausible causal null. Two paths are certified independently: PATH-BESPOKE
(the AK harness itself, an Unsloth `FastLanguageModel.for_inference` load)
and PATH-TUNER (the go-forward mechinterp `register_forward_hook` path on
plain-HF, already used by the resolved doubt-gated caution snap).

Resolved 2026-07-13. **Neither path is certified as an answer-window
steering instrument; the falsifier's quarantine binds on both.**
PATH-BESPOKE fails the firing gate on all 25 pinned prompts: the hook fires
exactly once per sequence, at prefill, never during the following 15 decode
steps, certifying the AK section 8 confound as instrumentation rather than a
causal null
([[unsloth-for-inference-decode-bypasses-steering-hook]]). PATH-TUNER
passes the firing gate (one call per decode step, all 25 prompts) and the
no-op gate (hidden state and logits exactly reproduce the hook-absent run
when the commanded write is zero), but fails the write-fidelity gate as
registered: 86 of 375 instrumented positions miss the 5% readback tolerance,
entirely at or after each prompt's own first behavioral divergence position,
with all 277 pre-divergence positions reading back 0.996-0.998 of commanded
([[cross-trajectory-readback-fails-after-intervention-diverges]]). Both
findings are recorded as characterization, not certification: the gates are
final and do not move after the run, so PATH-TUNER certification is left
open to a successor amendment with a divergence-robust readback design.
Source of truth: `experiments/h6-genstream-hook-firing-check/AMENDMENT.md`.
