---
schema_version: research-session/v1
session_id: 20260717T201649Z-margin-cascade-execution-m1-m2-m1b-m4
title: 'Margin cascade execution: M1 M2 M1b M4'
status: active
created_at: '2026-07-17T20:16:49Z'
updated_at: '2026-07-17T20:18:01Z'
question: Do the framework's margin-theory claims (1, 3) and the mentalistic-naming
  criteria hold at the qwen mid-band operating point, tested cheap-first through the
  M1-M6 cascade?
tags:
- margin-theory
- qwen-only-spine
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-checkpoint
  at: '2026-07-17T20:17:03Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M1 (margin-mapping) RESOLVED FALSIFIED, PR#299: qwen mid-band margins
    mechanically real and correctly placed (P2/P3/C1 pass) but the registered censoring-aware
    separation bound came out 2.0 vs floor 2.5; mistral void by instrument loss. M2
    (susceptibility-as-probe) RESOLVED FALSIFIED, PR#300: readout and margin channels
    REDUNDANT at qwen mid-band (incremental AUROC 0.0154 vs floor 0.02, readout alone
    0.982); verbalized confidence void by parse gate and descriptively anti-predictive
    (0.148). Claim 3 dissociation rejected here.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 002-checkpoint
  at: '2026-07-17T20:18:01Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M1b (margin-separation-fine-ladder) signed then RESOLVED null-result,
    PR#301: fine-ladder retest of M1''s separation criterion HALTED at its pre-registered
    RG0 byte-repro drift check. Diagnostics: detector-bit stability 98% but 2/53 refined
    rows break bracket on regeneration; row-131 tipping bit flips across batch sizes
    1/4/8 = stochastic bf16 batch-composition non-determinism, NOT env rot. PI chose
    Option 2 (no rework). Verdict: qwen mid-band margin separation is instrument-resolution-limited
    at the boundary; M1 Claim 1 falsification stands; miss is neither clean quantization
    nor clean real separation. DURABLE INSTRUMENT LESSON: byte-identical reuse guard
    is the wrong bar under bf16 batched greedy decoding (output depends on batch composition);
    a self-consistent single-regime run (pinned batch / bs-1) is the only reproducible
    instrument. Process upgrade held all cascade: red-team the DRAFT before PI signature.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-checkpoint
  at: '2026-07-17T20:18:01Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M4 (margin-evidence-responsiveness) DRAFTED + red-team in flight; PI gave
    conditional sign authorization (sign unless red-team finds something prediction-changing).
    Tests earnability criterion (d) on qwen c_hat: true-answer-in-context should (1)
    COLLAPSE the projection toward known regime and (2) LENGTHEN the margin. Within-row
    paired, 3 arms (no-answer/true-answer/false-answer placebo for specificity), single
    batching regime (M1b lesson), 2896 model passes on local 3090. Channel 1 = projection
    collapse (capture, floor 0.5x baseline gap 1.9484 = 0.9742, plus specificity CI
    vs placebo); Channel 2 = single-dose survival at each row''s own M1 tipping dose
    (308 eligible confab rows, floor 0.056). Both channels required for (d); single-channel
    pass = reported dissociation. Baseline projection: confab 3.0005 vs known 1.0521.
    Scoreboard provisional: PI predicts SPLIT (projection collapses, margin does not)
    + projection stronger; orchestrator leans EARNED (both) + projection stronger.
    Seeds 48260721/722/723. NEXT: apply red-team fixes, register scoreboards, sign,
    build (harness-builder, GPU preflight mandatory), then M4 run. After M4: family
    decision memo (retire llama/mistral for gemma?) before M3; M5 training bridge;
    M6 scale.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
track: margin-theory-cascade
---
# Margin cascade execution: M1 M2 M1b M4

## Question

Do the framework's margin-theory claims (1, 3) and the mentalistic-naming criteria hold at the qwen mid-band operating point, tested cheap-first through the M1-M6 cascade?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-checkpoint - Checkpoint

- at: `2026-07-17T20:17:03Z`
- kind: `checkpoint`
- summary: M1 (margin-mapping) RESOLVED FALSIFIED, PR#299: qwen mid-band margins mechanically real and correctly placed (P2/P3/C1 pass) but the registered censoring-aware separation bound came out 2.0 vs floor 2.5; mistral void by instrument loss. M2 (susceptibility-as-probe) RESOLVED FALSIFIED, PR#300: readout and margin channels REDUNDANT at qwen mid-band (incremental AUROC 0.0154 vs floor 0.02, readout alone 0.982); verbalized confidence void by parse gate and descriptively anti-predictive (0.148). Claim 3 dissociation rejected here.
### 002-checkpoint - Checkpoint

- at: `2026-07-17T20:18:01Z`
- kind: `checkpoint`
- summary: M1b (margin-separation-fine-ladder) signed then RESOLVED null-result, PR#301: fine-ladder retest of M1's separation criterion HALTED at its pre-registered RG0 byte-repro drift check. Diagnostics: detector-bit stability 98% but 2/53 refined rows break bracket on regeneration; row-131 tipping bit flips across batch sizes 1/4/8 = stochastic bf16 batch-composition non-determinism, NOT env rot. PI chose Option 2 (no rework). Verdict: qwen mid-band margin separation is instrument-resolution-limited at the boundary; M1 Claim 1 falsification stands; miss is neither clean quantization nor clean real separation. DURABLE INSTRUMENT LESSON: byte-identical reuse guard is the wrong bar under bf16 batched greedy decoding (output depends on batch composition); a self-consistent single-regime run (pinned batch / bs-1) is the only reproducible instrument. Process upgrade held all cascade: red-team the DRAFT before PI signature.
### 003-checkpoint - Checkpoint

- at: `2026-07-17T20:18:01Z`
- kind: `checkpoint`
- summary: M4 (margin-evidence-responsiveness) DRAFTED + red-team in flight; PI gave conditional sign authorization (sign unless red-team finds something prediction-changing). Tests earnability criterion (d) on qwen c_hat: true-answer-in-context should (1) COLLAPSE the projection toward known regime and (2) LENGTHEN the margin. Within-row paired, 3 arms (no-answer/true-answer/false-answer placebo for specificity), single batching regime (M1b lesson), 2896 model passes on local 3090. Channel 1 = projection collapse (capture, floor 0.5x baseline gap 1.9484 = 0.9742, plus specificity CI vs placebo); Channel 2 = single-dose survival at each row's own M1 tipping dose (308 eligible confab rows, floor 0.056). Both channels required for (d); single-channel pass = reported dissociation. Baseline projection: confab 3.0005 vs known 1.0521. Scoreboard provisional: PI predicts SPLIT (projection collapses, margin does not) + projection stronger; orchestrator leans EARNED (both) + projection stronger. Seeds 48260721/722/723. NEXT: apply red-team fixes, register scoreboards, sign, build (harness-builder, GPU preflight mandatory), then M4 run. After M4: family decision memo (retire llama/mistral for gemma?) before M3; M5 training bridge; M6 scale.
