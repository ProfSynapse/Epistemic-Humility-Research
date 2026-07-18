---
schema_version: research-session/v1
session_id: 20260717T201649Z-margin-cascade-execution-m1-m2-m1b-m4
title: 'Margin cascade execution: M1 M2 M1b M4'
status: active
created_at: '2026-07-17T20:16:49Z'
updated_at: '2026-07-18T11:33:27Z'
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
- id: 004-checkpoint
  at: '2026-07-17T20:44:00Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M4 (margin-evidence-responsiveness) SIGNED 2026-07-17 (2303dfe7, red-team
    fixes applied: before-question anchor + fresh-baseline S1 gate) then found VOID-BY-DESIGN
    at build: the true_answer/false_answer arms require gold answers but all 400 confab
    rows are KUQ world-UNKNOWN questions whose source (datasets/kuq/unknowns_all.jsonl)
    has NO answer field. Verified 3 ways: subsample confab prefixes all kuq_unknowns_all,
    staged aliases empty for every confab row, source keys carry no answer/gold field.
    Root cause: criterion (d) "supply the true answer" presupposes a world-KNOWN answer,
    but the qwen c_hat direction is fit on world-UNKNOWN questions, so (d) is ill-posed
    on its own population; (a)-(c) stand, (d) unadjudicated. Evaded sign + full red-team
    because the self-blinded design derivation reproduced the reused instrument median/AUROC
    exactly but never touched the new arms row text. DURABLE LESSON captured in the
    experiment-runner skill (PR#302, awaiting merge): pre-sign feasibility probe -
    verify every injected/consumed field exists and is non-empty on the test-population
    id list, allowed and REQUIRED even under self-blinding; distinguish world-unknown
    (no answer for anyone) from model-unknown (answer exists, model lacks it). PI
    DECISION: full REBASE onto a world-KNOWN confab population (popqa 14.3K / triviaqa
    have gold answers), guiding principle = MAXIMIZE DATA REUSE (artifacts recyclable
    for M3/M5/family + public data-exhaust). Data scout confirmed datasets ready but
    no existing qwen confab-vs-correct labels, no world-known direction, no margin
    data outside M1s set, so the rebase needs fresh generation + labeling + margin
    ladder (~several h 3090) + a fresh sign. Design derivation in flight (m4wk-design-derivation):
    dataset choice, confab/correctness/abstention rules, three role-group counts,
    direction fork (KUQ-transfer + native world-known c_hat fit), channels 1/2 with
    re-derived floors, reusable-artifact manifest, and the pre-sign feasibility probe
    M4 skipped. NEXT: red-team the derivation draft, lift design forks to PI (dataset,
    native-vs-transfer primary, subset sizes, publish-as-exhaust intent), resolve
    void M4 as superseded, sign the rebase, then build. After: family memo (retire
    llama/mistral for gemma?) before M3; M5; M6.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 005-checkpoint
  at: '2026-07-18T11:33:27Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'M4-WK signed (b98a1ef1) and executed through the firing gate. Census:
    14267 PopQA rows (confab 11048 / correct 2744 / refused 421, ~77% confab rate
    on Qwen3.5-4B). SC0 selection + distractor mapping committed pre-generation; native
    fit + cell.yaml repin (432ca7fa). FIRING GATE: transfer (KUQ-fit) baseline confab-vs-correct
    AUROC 0.3018 [0.2647,0.3396], below chance; gap_z -0.181. Independent sign-flip
    verification (results-analyst): VERDICT SIGN CORRECT - KUQ reproduction under
    identical harness code gives AUROC 0.987 (a flip would give 0.013), and raw projections
    genuinely reverse between populations (KUQ confab more-negative, world-known confab
    more-POSITIVE). Transfer primary criterion (d) VOID per BLOCKER B1 (void-and-lift,
    never scored not-earned). Native direction fires: AUROC 0.8628, gap +1.642, fit/test
    reproduction within 0.05. Key finding: the doubt direction fires where (d) cannot
    be run (world-unknown) and does not fire where it can (world-known); only the
    purpose-refit native direction fires there, carrying fit-circularity. PI DECISION:
    full native two-channel secondary dissociation (D1 from existing captures; native-only
    channel-2 ladder + survival on 3090; transfer dropped from channel-2). Process
    fixes this arc: three harness bugs caught pre-GPU by build agent (env-var mismatch,
    dropped mu_c term - verified inert, sidecar field misread); lead adjudications
    A/C confirmed, B = lead-run blinded grading with isolated adjudicator (build agent
    is a leaking context); recurring detached-nohup stall fixed (harness-tracked launches
    + persistent lead-side stall monitor; skill PR in flight); blinded-grading protocol
    pre-written. NEXT: native D1+D2, S1 channel-2 gate, grading-shard handoff, lead
    adjudication, resolve + PR (merge needs PI approval).'
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
### 004-checkpoint - Checkpoint

- at: `2026-07-17T20:44:00Z`
- kind: `checkpoint`
- summary: M4 (margin-evidence-responsiveness) SIGNED 2026-07-17 (2303dfe7, red-team fixes applied: before-question anchor + fresh-baseline S1 gate) then found VOID-BY-DESIGN at build: the true_answer/false_answer arms require gold answers but all 400 confab rows are KUQ world-UNKNOWN questions whose source (datasets/kuq/unknowns_all.jsonl) has NO answer field. Verified 3 ways: subsample confab prefixes all kuq_unknowns_all, staged aliases empty for every confab row, source keys carry no answer/gold field. Root cause: criterion (d) "supply the true answer" presupposes a world-KNOWN answer, but the qwen c_hat direction is fit on world-UNKNOWN questions, so (d) is ill-posed on its own population; (a)-(c) stand, (d) unadjudicated. Evaded sign + full red-team because the self-blinded design derivation reproduced the reused instrument median/AUROC exactly but never touched the new arms row text. DURABLE LESSON captured in the experiment-runner skill (PR#302, awaiting merge): pre-sign feasibility probe - verify every injected/consumed field exists and is non-empty on the test-population id list, allowed and REQUIRED even under self-blinding; distinguish world-unknown (no answer for anyone) from model-unknown (answer exists, model lacks it). PI DECISION: full REBASE onto a world-KNOWN confab population (popqa 14.3K / triviaqa have gold answers), guiding principle = MAXIMIZE DATA REUSE (artifacts recyclable for M3/M5/family + public data-exhaust). Data scout confirmed datasets ready but no existing qwen confab-vs-correct labels, no world-known direction, no margin data outside M1s set, so the rebase needs fresh generation + labeling + margin ladder (~several h 3090) + a fresh sign. Design derivation in flight (m4wk-design-derivation): dataset choice, confab/correctness/abstention rules, three role-group counts, direction fork (KUQ-transfer + native world-known c_hat fit), channels 1/2 with re-derived floors, reusable-artifact manifest, and the pre-sign feasibility probe M4 skipped. NEXT: red-team the derivation draft, lift design forks to PI (dataset, native-vs-transfer primary, subset sizes, publish-as-exhaust intent), resolve void M4 as superseded, sign the rebase, then build. After: family memo (retire llama/mistral for gemma?) before M3; M5; M6.
### 005-checkpoint - Checkpoint

- at: `2026-07-18T11:33:27Z`
- kind: `checkpoint`
- summary: M4-WK signed (b98a1ef1) and executed through the firing gate. Census: 14267 PopQA rows (confab 11048 / correct 2744 / refused 421, ~77% confab rate on Qwen3.5-4B). SC0 selection + distractor mapping committed pre-generation; native fit + cell.yaml repin (432ca7fa). FIRING GATE: transfer (KUQ-fit) baseline confab-vs-correct AUROC 0.3018 [0.2647,0.3396], below chance; gap_z -0.181. Independent sign-flip verification (results-analyst): VERDICT SIGN CORRECT - KUQ reproduction under identical harness code gives AUROC 0.987 (a flip would give 0.013), and raw projections genuinely reverse between populations (KUQ confab more-negative, world-known confab more-POSITIVE). Transfer primary criterion (d) VOID per BLOCKER B1 (void-and-lift, never scored not-earned). Native direction fires: AUROC 0.8628, gap +1.642, fit/test reproduction within 0.05. Key finding: the doubt direction fires where (d) cannot be run (world-unknown) and does not fire where it can (world-known); only the purpose-refit native direction fires there, carrying fit-circularity. PI DECISION: full native two-channel secondary dissociation (D1 from existing captures; native-only channel-2 ladder + survival on 3090; transfer dropped from channel-2). Process fixes this arc: three harness bugs caught pre-GPU by build agent (env-var mismatch, dropped mu_c term - verified inert, sidecar field misread); lead adjudications A/C confirmed, B = lead-run blinded grading with isolated adjudicator (build agent is a leaking context); recurring detached-nohup stall fixed (harness-tracked launches + persistent lead-side stall monitor; skill PR in flight); blinded-grading protocol pre-written. NEXT: native D1+D2, S1 channel-2 gate, grading-shard handoff, lead adjudication, resolve + PR (merge needs PI approval).
