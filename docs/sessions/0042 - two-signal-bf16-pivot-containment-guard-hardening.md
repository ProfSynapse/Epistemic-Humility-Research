---
schema_version: research-session/v1
session_id: '0042'
title: Two-signal bf16 substrate pivot; dataset containment + guard/skill hardening;
  J-lens built
status: active
created_at: '2026-07-07T12:36:11Z'
updated_at: '2026-07-07T17:24:49Z'
phase: CODE
question: Does two-signal caution regulation actuate bidirectionally on raw-base Qwen3-4B
  once the whole instrument is moved to full bf16 (unifying substrate with the bf16-only
  J-lens), and can the program's public-repo data containment plus subagent guardrails
  be hardened without losing evidence?
tags:
- two-signal
- bf16
- containment
- j-space
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-decision
  at: '2026-07-07T12:36:11Z'
  kind: decision
  title: bf16 substrate pivot decided
  summary: 'Verified the prior two-signal directions were fit on bnb-4bit (extract_l34_anchor.py
    load_in_4bit=True), NOT bf16. Per user request moved the ENTIRE experiment to
    full bf16 (unsloth/Qwen3-4B): fresh extraction, refit of all three directions,
    dose recalibration, and run model. This unifies the substrate with the bf16-only
    J-lens and removes the H1 cross-quantization caveat.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - Full bf16 pivot for two-signal; unsloth/Qwen3-4B mirror chosen (same tokenizer/chat
    template as the 4-bit repo).
  next_steps:
  - Refit on bf16, recalibrate dose to the bf16 window, re-smoke.
  signals: {}
- id: 002-infrastructure
  at: '2026-07-07T12:36:11Z'
  kind: infrastructure
  title: data-containment + lift-blocks rules; idle-guard hardened
  summary: 'PR #247 merged: pr-workflow skill now forbids committing datasets to the
    PUBLIC repo (stage to private HF professorsynapse/eh-al-prep-staging, commit ID-manifests
    + fitted-artifact JSON + code only) and requires subagents to LIFT a classifier/hook
    block to the lead rather than work around it (motivated by a J-lens builder that
    committed a 1000-row corpus after its HF upload was blocked). Also hardened ~/.claude/hooks/sendmessage_idle_guard.sh:
    it only recognized the teammate idleReason shape and falsely blocked follow-up
    sends to COMPLETED background agents; now it also treats a background task-notification
    completed status as an idle signal, and counts the spawn-result agentId as outbound
    (closing a fail-open hole where a fresh in-flight agent could be messaged). Verified
    against the live transcript.'
  evidence:
  - 'PR #247 (commit e3c2e08 -> merged 332d7dfe); hook file sendmessage_idle_guard.sh'
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-result
  at: '2026-07-07T12:36:11Z'
  kind: result
  title: bf16 refit complete, G0 pass, narrow-window caveat
  summary: 'Commit 2fcf8b21 on exp/two-signal-caution-regulation-instruct: fresh 1576-row
    bf16 extraction; all four direction files refit (u_d mean-diff 89 vs 1029; pos_ctrl
    mass-mean refuse-vs-confab; neg_ctrl standardized logistic; c_hat orthogonalized
    against u_d+neg_ctrl, cos 0.872, sigma_c 21.36 vs 4-bit 36.18). Eval pool migrated
    off committed question text to eval_pool_manifest.jsonl + materialize_eval_pool.py
    (HF fetch of a0 pool + join); git grep confirms zero tracked question text. G0
    re-smoke PASS: write_ok, parity_ok, gen_stream_fired, max_write_error 0.135 (down
    from 4-bit 0.755 as bf16 writes are smaller magnitude), 0/12 collapse. CAVEAT:
    the orthogonalized-c_hat coherent window is narrow and low (first coherent move
    ~20-27, collapse ~40-43); calibrated dose median ~25-31, clip 40 sits near the
    low edge with per-row heterogeneity, so behavioral headroom is thin and a weak
    or tighten-only outcome is a live possibility (covered by the pre-stated falsifier).'
  evidence:
  - commit 2fcf8b21; analysis/dose_ladder_bf16_ambient_relative_results.jsonl
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 004-planning
  at: '2026-07-07T12:36:11Z'
  kind: planning
  title: 'next steps: red-team, sign, sweep; J-lens launch'
  summary: 'Red-team of the bf16 instrument is running (oracle-leak/circularity, dose
    sub-threshold vs collapse-adjacent-clip, grader is_degenerate JSON strip, placebo
    integrity, gates-unchanged). On clear: lead signs (user pre-authorized) then runs
    the 458-row sweep on the free local 3090, red-teams the results, resolves and
    PRs (squash-merge to keep intermediate question-text blobs off public main). J-lens
    (branch exp/j-space-localization-qwen3-4b; harness + containment done, doc fixes
    at 6c2f42f9) ships to Modal AFTER the bf16 directions are swapped in, REPO_COMMIT
    re-pinned, and the branch pushed; needs fresh user launch approval (~3-4 USD,
    25 USD cap).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Await red-team; sign + local sweep; then resolve. J-lens Modal launch pending
    bf16-direction swap + user approval.
  signals: {}
- id: 005-checkpoint
  at: '2026-07-07T14:03:39Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Two-signal red-team -> KILL confirmed -> fixed -> corrected-dose smoke
    exposed a deeper viability failure -> user reframe to gate-and-snap -> free diagnostic
    running.


    RED-TEAM KILL (confirmed in tuner source): the bf16 dose sweep fed strength=k*ambient
    as the GAIN into the real erase_write hook (sigma=21.36), and hooks.py docstring
    L7-12 shows the law writes gain*sigma as the realized projection. So the sweep
    coherent-move at strength ~24.8 realized a projection ~530, but the run commanded
    marginal_write ~25 (smoke readback 24.95) -> ~20x under-dosed, guaranteed false
    null on the novel release half. 0/12 tighten flips in the prior smoke was the
    signature.


    FIX (commit 8f277410 on exp/two-signal-caution-regulation-instruct): added hook.last_readback
    logging, re-ran sweep in readback units (coherent move median |readback|=531.9,
    collapse median 952, confab-cell collapse 808 the tighter bound). ALPHA 2.0->40.0,
    MARGINAL_WRITE_CLIP 40.0->750.0. materialize_eval_pool.py now hard-fails on empty
    aliases. AMENDMENT/cell.yaml/NOTEBOOK G0 window reconciled to readback units.


    VIABILITY FAILURE (reading the actual generations, not the summary): corrected-dose
    re-smoke -> RELEASE half 0/6 at every dose: negating c_hat leaves refusal intact
    at low write or shatters into token-spam (yes yes yes / I-don-t-know xN) at high
    write; never synthesizes a correct answer (even Terry Gilliam->Time Bandits produced
    yes-yes-yes at -750). TIGHTEN 1/6 clean, and the degeneracy detector UNDER-COUNTS:
    4/6 confab rows scored deg=0 were actually I"I"I token-spam garbage. Mechanism:
    c_hat is functionally a say-I-dont-know axis; +c_hat weakly tightens then spams
    the I token, -c_hat cannot manufacture knowledge. VERDICT: DO NOT SIGN / DO NOT
    RUN as configured. #8 sign BLOCKED.


    KEY REFRAME (user): the scalar SCATTERS dose. Of 6 confab rows only the one at
    realized proj ~229 flipped clean; ~7 did nothing, 518/606/647/750 all garbaged.
    So the 1/6 is a dose-scatter artifact, not a ceiling. Redesign = GATE (fire when
    sensor evidence clears threshold tau) + SNAP to a FIXED optimal setpoint s* (sweet
    spot, NOT the maximum which is garbage). Both numbers are mathable: tau from ROC/Youden
    on existing z_doubt/z_confab vs confab labels (CPU), s* from a dose-response P(clean
    refuse) curve peak (local 3090). Release abandoned; tighten-only.


    DIAGNOSTIC running (agent a7d9699da37b1549f, free local 3090, exploratory scratch,
    NO amendment/sign/commit): step0 fix detector (verify vs known smoke rows), step1
    fit tau + false-flag cost on known-correct, step2 s* dose-response curve, step3
    headline = clean-flip rate at s* (Wilson CI) vs scalar 1/6 + false-refusal cost.
    Uses committed directions at 8f277410, no rebuild.


    OTHER DEFECTS found: (a) build_two_signal_directions.py LogisticRegression(saga)
    has no random_state -> neg_ctrl/c_hat non-reproducible (committed vectors cannot
    be regenerated); must pin before any signed instrument. (b) release pool appears
    contaminated with false-premise items (Who made the first telephone call to the
    Moon?) where release would be wrong anyway.


    NEXT: read diagnostic result. If gate-and-snap clearly beats 1/6 with acceptable
    false-refusal -> promote to a FRESH pre-registered amendment (thresholded-gate
    law) -- user is separately working on amendment AQ, so pick a NON-AQ slug and
    check the registry first. If not -> write the current two-signal up as a documented
    null (readout portable, single caution axis only adds refusal weakly, cannot release).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 006-checkpoint
  at: '2026-07-07T14:44:04Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Gate-and-snap diagnostic round 1 (agent a7d9699, DONE, free local 3090,
    exploratory scratch -- NO amendment/sign/commit) + round 2 dispatched.


    ROUND 1 FINDINGS:

    - GATE = a DOUBT threshold, and it is strong. Separability of confab vs known_correct_answered:
    neg_z_d (doubt) AUC 0.976; combined (z_p - z_d) 0.867; z_p (confab-propensity)
    alone 0.213 (inverted/off-task). Youden tau: 94.5% of confabs caught, 4.5% of
    known-correct false-flagged. So the tighten gate is effectively ONE-signal (doubt);
    the "two-signal" coupling does not survive the data for tighten. Caveat: known_correct
    is in-sample to the u_d fit, so 0.976 is a bit optimistic.

    - CONFAB-PROPENSITY (neg_ctrl) is NOT junk -- it was tested on the wrong contrast.
    neg_ctrl was fit (build L280-285) as logistic confab(1) vs unknown_refused(0)
    over the 1,338-row AK Stage-1 pool -- i.e. among non-answers, fabricate vs abstain.
    That is its designed job; it is merely off-task for confab-vs-correct (the doubt
    axis owns that). Round 2 will confirm its AUC on its own held-out contrast.

    - TIGHTEN is real and dose-dependent. Semantic refuse (first parsed answer field):
    8% @readback50, 25%@100, 58%@150, 71%@200, 79%@250, 83%@300-350, then collapse
    (0%, 22/24 garbage) @600. So the earlier scalar 1/6 was a dose-SCATTER artifact
    (only 1 of 6 confab rows landed near the coherent band), NOT a ceiling -- the
    reframe is vindicated on the semantic axis.

    - BUT the "clean stop" problem was mostly a HARNESS BUG, not the caution write.
    dose_escalation_bf16_ambient_relative.py:148 sets min_new_tokens=MAX_NEW alongside
    max_new_tokens=MAX_NEW, which FORCES exactly MAX_NEW tokens and SUPPRESSES EOS:
    the model produces a clean first JSON answer, cannot stop, and is forced to emit
    filler -- repeated answer + stray </think> at baseline (16/24 undosed rows), `}-empty`
    loops at dose 150-200, phrase-looping at 250+. The FIRST JSON object is clean
    at every non-collapse dose. So the "degeneration onset at 150" is largely a forced-continuation
    measurement artifact. (Ruled out enable_thinking scaffold as the cause: the </think>
    appears AFTER a complete answer, and baseline has no `-empty`.)

    - Step-3 payoff (old anchor_onward @ fixed readback 250, gate-free control): confab
    clean_flip (old detector) 28/80 = 35% (Wilson 25-46%); known_correct dosed at
    250 -> false_refusal 79/80 = 98.75%. So a fixed 250 write is a blunt hammer that
    nukes correct answers -- the gate is essential and 250 is too high.


    DEFECTS confirmed: (a) build LogisticRegression(saga) has no random_state -> neg_ctrl/c_hat
    non-reproducible (committed c_hat/neg_ctrl were rewritten in commit 8f277410);
    must pin before any signed instrument. (b) generation harness min_new_tokens bug
    (above). (c) release pool false-premise contamination (noted earlier).


    ROUND 2 dispatched (agent a3ef6d5e62793f6d4, RUNNING, free local 3090, scratch
    only): Step1 FIX generation -- remove min_new_tokens, enable EOS/<|im_end|> stop,
    enable_thinking=False, verify baseline terminates cleanly. Step2 dose(80-260)
    x write-scope(anchor_onward vs prompt-only-released-during-decode vs short-decay)
    sweep, honest metric clean_tighten = refuse AND natural termination. Step3 payoff
    at best cell: clean_tighten + Wilson CI on confab (~80) + false-refusal cost on
    known_correct (~80). Step4 CPU: re-grade old anchor@250 with clean_tighten; propensity-own-contrast
    AUC (confab vs unknown_refused).


    DECIDES: is there a (dose,scope) with high clean_tighten AND low false-refusal
    -> viable gate-and-snap tighten instrument, promote to a FRESH pre-registered
    amendment (NON-AQ; user is separately writing amendment AQ, do not collide). Else
    -> clean negative finding (caution write cannot induce a terminating refusal on
    bf16 raw-base).


    #8 two-signal sign remains BLOCKED (do not sign the proportional-scalar instrument;
    it is superseded by the gate-and-snap redesign under test).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 007-checkpoint
  at: '2026-07-07T17:24:49Z'
  kind: checkpoint
  title: Checkpoint
  summary: "DIAGNOSTIC COMPLETE -- gate-and-snap tighten is VIABLE; decided to draft\
    \ a fresh pre-registered amendment.\n\nFINAL step-3 payoff frontier (anchor_onward,\
    \ FIXED generation EOS-on, n=80/cell, local 3090):\n  dose 200: confab clean_tighten\
    \ 82.5% [73,89]; known-correct false-refuse 36.2% [27,47]; gated~ 78% tighten\
    \ / 1.6% false-refuse\n  dose 230: 86.2% [77,92]; 45.0% [35,56]; gated~ 82% /\
    \ 2.0%\n  dose 260: 87.5% [78,93]; 56.2% [45,67]; gated~ 83% / 2.5%\nDiminishing\
    \ returns: tighten +5pt from 200->260 while false-refuse +20pt. DOSE ~200 = selectivity\
    \ sweet spot.\n\nVERDICT: on bf16 raw-base, TRAINING-FREE, gate-and-snap tightens\
    \ selectively. Gate = DOUBT threshold (AUC 0.976; catches ~95% confab, flags ~5%\
    \ known-correct); snap = anchor_onward caution write at realized projection ~200;\
    \ generation EOS-enabled. Estimated gated: ~78% of confabs -> clean terminating\
    \ refusal, ~1.6% of correct answers wrongly refused. The write itself is NON-selective\
    \ (dosing a correct row refuses it 36% of the time); ALL selectivity comes from\
    \ the gate. RELEASE half remains a genuine null (documented). Diagnostic key corrections\
    \ vs the original proportional two-signal: (1) dose-units KILL fixed; (2) \"degeneration\"\
    \ was a harness bug (min_new_tokens==max_new_tokens suppressed EOS; 0/12->12/12\
    \ clean termination once fixed); (3) proportional scalar scattered dose (the 1/6\
    \ was scatter, not a ceiling); (4) the two-signal collapsed to a ONE-signal doubt\
    \ gate + caution snap; (5) neg_ctrl confirmed healthy on its OWN contrast (confab-vs-refuse\
    \ AUC 1.0 in-sample), just off-task for tighten.\n\nCAVEAT: gated numbers are\
    \ ESTIMATES (product of two separately-measured rates). Confirmatory needs an\
    \ END-TO-END gated run (gate decides dosing) on HELD-OUT, plus defects fixed:\
    \ pin random_state (reproducible directions), bake the generation fix into the\
    \ instrument, pre-register tau + dose 200.\n\nDECISION (user, 2026-07-07): DRAFT\
    \ a fresh pre-registered gate-and-snap amendment now (tighten-only, NON-AQ slug\
    \ -- user separately writing AQ), design = doubt-gated caution snap, confirmatory\
    \ = end-to-end gated pipeline on held-out with pre-stated tighten floor + false-refusal\
    \ ceiling + placebo (permuted-gate / random-direction) controls. Then user prediction\
    \ + exp sign + GPU approval (local 3090 free). #8 (old proportional-scalar sign)\
    \ stays superseded/BLOCKED.\n\nAll diagnostic artifacts under experiments/two-signal-caution-regulation-instruct/analysis/\
    \ (gitignored scratch): tighten_step1_* (gen fix), tighten_step2_* (dose x scope),\
    \ tighten_step3_d{200,230,260}_* (payoff), tighten_step4a/b (regrade + propensity\
    \ AUC), tighten_gen_lib.py (fixed generation)."
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
---
# Two-signal bf16 substrate pivot; dataset containment + guard/skill hardening; J-lens built

## Question

Does two-signal caution regulation actuate bidirectionally on raw-base Qwen3-4B once the whole instrument is moved to full bf16 (unifying substrate with the bf16-only J-lens), and can the program's public-repo data containment plus subagent guardrails be hardened without losing evidence?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-decision - bf16 substrate pivot decided

- at: `2026-07-07T12:36:11Z`
- kind: `decision`
- summary: Verified the prior two-signal directions were fit on bnb-4bit (extract_l34_anchor.py load_in_4bit=True), NOT bf16. Per user request moved the ENTIRE experiment to full bf16 (unsloth/Qwen3-4B): fresh extraction, refit of all three directions, dose recalibration, and run model. This unifies the substrate with the bf16-only J-lens and removes the H1 cross-quantization caveat.
- decisions:
  - Full bf16 pivot for two-signal; unsloth/Qwen3-4B mirror chosen (same tokenizer/chat template as the 4-bit repo).
- next steps:
  - Refit on bf16, recalibrate dose to the bf16 window, re-smoke.
### 002-infrastructure - data-containment + lift-blocks rules; idle-guard hardened

- at: `2026-07-07T12:36:11Z`
- kind: `infrastructure`
- summary: PR #247 merged: pr-workflow skill now forbids committing datasets to the PUBLIC repo (stage to private HF professorsynapse/eh-al-prep-staging, commit ID-manifests + fitted-artifact JSON + code only) and requires subagents to LIFT a classifier/hook block to the lead rather than work around it (motivated by a J-lens builder that committed a 1000-row corpus after its HF upload was blocked). Also hardened ~/.claude/hooks/sendmessage_idle_guard.sh: it only recognized the teammate idleReason shape and falsely blocked follow-up sends to COMPLETED background agents; now it also treats a background task-notification completed status as an idle signal, and counts the spawn-result agentId as outbound (closing a fail-open hole where a fresh in-flight agent could be messaged). Verified against the live transcript.
- evidence:
  - `PR #247 (commit e3c2e08 -> merged 332d7dfe); hook file sendmessage_idle_guard.sh`
### 003-result - bf16 refit complete, G0 pass, narrow-window caveat

- at: `2026-07-07T12:36:11Z`
- kind: `result`
- summary: Commit 2fcf8b21 on exp/two-signal-caution-regulation-instruct: fresh 1576-row bf16 extraction; all four direction files refit (u_d mean-diff 89 vs 1029; pos_ctrl mass-mean refuse-vs-confab; neg_ctrl standardized logistic; c_hat orthogonalized against u_d+neg_ctrl, cos 0.872, sigma_c 21.36 vs 4-bit 36.18). Eval pool migrated off committed question text to eval_pool_manifest.jsonl + materialize_eval_pool.py (HF fetch of a0 pool + join); git grep confirms zero tracked question text. G0 re-smoke PASS: write_ok, parity_ok, gen_stream_fired, max_write_error 0.135 (down from 4-bit 0.755 as bf16 writes are smaller magnitude), 0/12 collapse. CAVEAT: the orthogonalized-c_hat coherent window is narrow and low (first coherent move ~20-27, collapse ~40-43); calibrated dose median ~25-31, clip 40 sits near the low edge with per-row heterogeneity, so behavioral headroom is thin and a weak or tighten-only outcome is a live possibility (covered by the pre-stated falsifier).
- evidence:
  - `commit 2fcf8b21; analysis/dose_ladder_bf16_ambient_relative_results.jsonl`
### 004-planning - next steps: red-team, sign, sweep; J-lens launch

- at: `2026-07-07T12:36:11Z`
- kind: `planning`
- summary: Red-team of the bf16 instrument is running (oracle-leak/circularity, dose sub-threshold vs collapse-adjacent-clip, grader is_degenerate JSON strip, placebo integrity, gates-unchanged). On clear: lead signs (user pre-authorized) then runs the 458-row sweep on the free local 3090, red-teams the results, resolves and PRs (squash-merge to keep intermediate question-text blobs off public main). J-lens (branch exp/j-space-localization-qwen3-4b; harness + containment done, doc fixes at 6c2f42f9) ships to Modal AFTER the bf16 directions are swapped in, REPO_COMMIT re-pinned, and the branch pushed; needs fresh user launch approval (~3-4 USD, 25 USD cap).
- next steps:
  - Await red-team; sign + local sweep; then resolve. J-lens Modal launch pending bf16-direction swap + user approval.
### 005-checkpoint - Checkpoint

- at: `2026-07-07T14:03:39Z`
- kind: `checkpoint`
- summary: Two-signal red-team -> KILL confirmed -> fixed -> corrected-dose smoke exposed a deeper viability failure -> user reframe to gate-and-snap -> free diagnostic running.

RED-TEAM KILL (confirmed in tuner source): the bf16 dose sweep fed strength=k*ambient as the GAIN into the real erase_write hook (sigma=21.36), and hooks.py docstring L7-12 shows the law writes gain*sigma as the realized projection. So the sweep coherent-move at strength ~24.8 realized a projection ~530, but the run commanded marginal_write ~25 (smoke readback 24.95) -> ~20x under-dosed, guaranteed false null on the novel release half. 0/12 tighten flips in the prior smoke was the signature.

FIX (commit 8f277410 on exp/two-signal-caution-regulation-instruct): added hook.last_readback logging, re-ran sweep in readback units (coherent move median |readback|=531.9, collapse median 952, confab-cell collapse 808 the tighter bound). ALPHA 2.0->40.0, MARGINAL_WRITE_CLIP 40.0->750.0. materialize_eval_pool.py now hard-fails on empty aliases. AMENDMENT/cell.yaml/NOTEBOOK G0 window reconciled to readback units.

VIABILITY FAILURE (reading the actual generations, not the summary): corrected-dose re-smoke -> RELEASE half 0/6 at every dose: negating c_hat leaves refusal intact at low write or shatters into token-spam (yes yes yes / I-don-t-know xN) at high write; never synthesizes a correct answer (even Terry Gilliam->Time Bandits produced yes-yes-yes at -750). TIGHTEN 1/6 clean, and the degeneracy detector UNDER-COUNTS: 4/6 confab rows scored deg=0 were actually I"I"I token-spam garbage. Mechanism: c_hat is functionally a say-I-dont-know axis; +c_hat weakly tightens then spams the I token, -c_hat cannot manufacture knowledge. VERDICT: DO NOT SIGN / DO NOT RUN as configured. #8 sign BLOCKED.

KEY REFRAME (user): the scalar SCATTERS dose. Of 6 confab rows only the one at realized proj ~229 flipped clean; ~7 did nothing, 518/606/647/750 all garbaged. So the 1/6 is a dose-scatter artifact, not a ceiling. Redesign = GATE (fire when sensor evidence clears threshold tau) + SNAP to a FIXED optimal setpoint s* (sweet spot, NOT the maximum which is garbage). Both numbers are mathable: tau from ROC/Youden on existing z_doubt/z_confab vs confab labels (CPU), s* from a dose-response P(clean refuse) curve peak (local 3090). Release abandoned; tighten-only.

DIAGNOSTIC running (agent a7d9699da37b1549f, free local 3090, exploratory scratch, NO amendment/sign/commit): step0 fix detector (verify vs known smoke rows), step1 fit tau + false-flag cost on known-correct, step2 s* dose-response curve, step3 headline = clean-flip rate at s* (Wilson CI) vs scalar 1/6 + false-refusal cost. Uses committed directions at 8f277410, no rebuild.

OTHER DEFECTS found: (a) build_two_signal_directions.py LogisticRegression(saga) has no random_state -> neg_ctrl/c_hat non-reproducible (committed vectors cannot be regenerated); must pin before any signed instrument. (b) release pool appears contaminated with false-premise items (Who made the first telephone call to the Moon?) where release would be wrong anyway.

NEXT: read diagnostic result. If gate-and-snap clearly beats 1/6 with acceptable false-refusal -> promote to a FRESH pre-registered amendment (thresholded-gate law) -- user is separately working on amendment AQ, so pick a NON-AQ slug and check the registry first. If not -> write the current two-signal up as a documented null (readout portable, single caution axis only adds refusal weakly, cannot release).
### 006-checkpoint - Checkpoint

- at: `2026-07-07T14:44:04Z`
- kind: `checkpoint`
- summary: Gate-and-snap diagnostic round 1 (agent a7d9699, DONE, free local 3090, exploratory scratch -- NO amendment/sign/commit) + round 2 dispatched.

ROUND 1 FINDINGS:
- GATE = a DOUBT threshold, and it is strong. Separability of confab vs known_correct_answered: neg_z_d (doubt) AUC 0.976; combined (z_p - z_d) 0.867; z_p (confab-propensity) alone 0.213 (inverted/off-task). Youden tau: 94.5% of confabs caught, 4.5% of known-correct false-flagged. So the tighten gate is effectively ONE-signal (doubt); the "two-signal" coupling does not survive the data for tighten. Caveat: known_correct is in-sample to the u_d fit, so 0.976 is a bit optimistic.
- CONFAB-PROPENSITY (neg_ctrl) is NOT junk -- it was tested on the wrong contrast. neg_ctrl was fit (build L280-285) as logistic confab(1) vs unknown_refused(0) over the 1,338-row AK Stage-1 pool -- i.e. among non-answers, fabricate vs abstain. That is its designed job; it is merely off-task for confab-vs-correct (the doubt axis owns that). Round 2 will confirm its AUC on its own held-out contrast.
- TIGHTEN is real and dose-dependent. Semantic refuse (first parsed answer field): 8% @readback50, 25%@100, 58%@150, 71%@200, 79%@250, 83%@300-350, then collapse (0%, 22/24 garbage) @600. So the earlier scalar 1/6 was a dose-SCATTER artifact (only 1 of 6 confab rows landed near the coherent band), NOT a ceiling -- the reframe is vindicated on the semantic axis.
- BUT the "clean stop" problem was mostly a HARNESS BUG, not the caution write. dose_escalation_bf16_ambient_relative.py:148 sets min_new_tokens=MAX_NEW alongside max_new_tokens=MAX_NEW, which FORCES exactly MAX_NEW tokens and SUPPRESSES EOS: the model produces a clean first JSON answer, cannot stop, and is forced to emit filler -- repeated answer + stray </think> at baseline (16/24 undosed rows), `}-empty` loops at dose 150-200, phrase-looping at 250+. The FIRST JSON object is clean at every non-collapse dose. So the "degeneration onset at 150" is largely a forced-continuation measurement artifact. (Ruled out enable_thinking scaffold as the cause: the </think> appears AFTER a complete answer, and baseline has no `-empty`.)
- Step-3 payoff (old anchor_onward @ fixed readback 250, gate-free control): confab clean_flip (old detector) 28/80 = 35% (Wilson 25-46%); known_correct dosed at 250 -> false_refusal 79/80 = 98.75%. So a fixed 250 write is a blunt hammer that nukes correct answers -- the gate is essential and 250 is too high.

DEFECTS confirmed: (a) build LogisticRegression(saga) has no random_state -> neg_ctrl/c_hat non-reproducible (committed c_hat/neg_ctrl were rewritten in commit 8f277410); must pin before any signed instrument. (b) generation harness min_new_tokens bug (above). (c) release pool false-premise contamination (noted earlier).

ROUND 2 dispatched (agent a3ef6d5e62793f6d4, RUNNING, free local 3090, scratch only): Step1 FIX generation -- remove min_new_tokens, enable EOS/<|im_end|> stop, enable_thinking=False, verify baseline terminates cleanly. Step2 dose(80-260) x write-scope(anchor_onward vs prompt-only-released-during-decode vs short-decay) sweep, honest metric clean_tighten = refuse AND natural termination. Step3 payoff at best cell: clean_tighten + Wilson CI on confab (~80) + false-refusal cost on known_correct (~80). Step4 CPU: re-grade old anchor@250 with clean_tighten; propensity-own-contrast AUC (confab vs unknown_refused).

DECIDES: is there a (dose,scope) with high clean_tighten AND low false-refusal -> viable gate-and-snap tighten instrument, promote to a FRESH pre-registered amendment (NON-AQ; user is separately writing amendment AQ, do not collide). Else -> clean negative finding (caution write cannot induce a terminating refusal on bf16 raw-base).

#8 two-signal sign remains BLOCKED (do not sign the proportional-scalar instrument; it is superseded by the gate-and-snap redesign under test).
### 007-checkpoint - Checkpoint

- at: `2026-07-07T17:24:49Z`
- kind: `checkpoint`
- summary: DIAGNOSTIC COMPLETE -- gate-and-snap tighten is VIABLE; decided to draft a fresh pre-registered amendment.

FINAL step-3 payoff frontier (anchor_onward, FIXED generation EOS-on, n=80/cell, local 3090):
  dose 200: confab clean_tighten 82.5% [73,89]; known-correct false-refuse 36.2% [27,47]; gated~ 78% tighten / 1.6% false-refuse
  dose 230: 86.2% [77,92]; 45.0% [35,56]; gated~ 82% / 2.0%
  dose 260: 87.5% [78,93]; 56.2% [45,67]; gated~ 83% / 2.5%
Diminishing returns: tighten +5pt from 200->260 while false-refuse +20pt. DOSE ~200 = selectivity sweet spot.

VERDICT: on bf16 raw-base, TRAINING-FREE, gate-and-snap tightens selectively. Gate = DOUBT threshold (AUC 0.976; catches ~95% confab, flags ~5% known-correct); snap = anchor_onward caution write at realized projection ~200; generation EOS-enabled. Estimated gated: ~78% of confabs -> clean terminating refusal, ~1.6% of correct answers wrongly refused. The write itself is NON-selective (dosing a correct row refuses it 36% of the time); ALL selectivity comes from the gate. RELEASE half remains a genuine null (documented). Diagnostic key corrections vs the original proportional two-signal: (1) dose-units KILL fixed; (2) "degeneration" was a harness bug (min_new_tokens==max_new_tokens suppressed EOS; 0/12->12/12 clean termination once fixed); (3) proportional scalar scattered dose (the 1/6 was scatter, not a ceiling); (4) the two-signal collapsed to a ONE-signal doubt gate + caution snap; (5) neg_ctrl confirmed healthy on its OWN contrast (confab-vs-refuse AUC 1.0 in-sample), just off-task for tighten.

CAVEAT: gated numbers are ESTIMATES (product of two separately-measured rates). Confirmatory needs an END-TO-END gated run (gate decides dosing) on HELD-OUT, plus defects fixed: pin random_state (reproducible directions), bake the generation fix into the instrument, pre-register tau + dose 200.

DECISION (user, 2026-07-07): DRAFT a fresh pre-registered gate-and-snap amendment now (tighten-only, NON-AQ slug -- user separately writing AQ), design = doubt-gated caution snap, confirmatory = end-to-end gated pipeline on held-out with pre-stated tighten floor + false-refusal ceiling + placebo (permuted-gate / random-direction) controls. Then user prediction + exp sign + GPU approval (local 3090 free). #8 (old proportional-scalar sign) stays superseded/BLOCKED.

All diagnostic artifacts under experiments/two-signal-caution-regulation-instruct/analysis/ (gitignored scratch): tighten_step1_* (gen fix), tighten_step2_* (dose x scope), tighten_step3_d{200,230,260}_* (payoff), tighten_step4a/b (regrade + propensity AUC), tighten_gen_lib.py (fixed generation).
