---
schema_version: research-session/v1
session_id: '0038'
title: Amendment AI NULL verdict (G1 inverted) and AL prep on the TRUE checkpoint (internals characterization + drift decomposition)
status: active
created_at: '2026-07-05T09:00:00Z'
updated_at: '2026-07-05T14:05:00Z'
phase: phase1
question: >-
  Amendment AI adjudication: did probe-as-reward GRPO train the model to
  consult its own readout? Then, for the AL pivot: what did the sensor-reward
  training actually change inside the TRUE checkpoint, measured against the
  program's named epistemic axes?
tags:
- amendment-ai
- amendment-al
- probe-as-reward
- radial-steering
- mech-interp
- experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: >-
    Amendment AI resolved NULL with an INVERTED G1 (TRUE congruence 59.75 vs
    PERMUTED 76.75, -17.0pt, CI [-21.5, -12.5]); the reward channel joins M/N/
    R/AA/AB as a use-the-signal null - five channels now agree the model
    cannot be trained to consult its readout, while external readers remain
    fully effective. The program pivots to radial steering (Amendment AL) ON
    the AI-TRUE checkpoint, user-directed. CPU characterization shows the
    readout untouched (transfer ~1.0), drift ~98 percent off-axis, and the
    sensor-specific displacement organized by label but orthogonal to every
    named axis.
  changed_by_session: >-
    AI closed (PR #207, staging dataset repo deleted, scoreboard TIE/TIE,
    tally user 3 - orch 2 - ties 2; seeds backlogged by the user). AL branch
    opened with two committed CPU characterization instruments and their
    first results; GRPO-v2 union extraction launched for the four-way;
    RunPod job lane landed in Synaptic-Tuner (PRs #125/#126) with the
    research-repo submodule repointed (PR #206).
checkpoints:
- id: 001-result
  at: '2026-07-05T11:40:00Z'
  kind: result
  title: 'All-local verdict evidence complete: four extract cells + both generations on one lane after the cloud lane was abandoned'
  summary: >-
    Four HF Jobs nodes in one day had broken networking (two generate nodes
    stalled at 200-400 kB/s on the base shard; one extract cell sat RUNNING
    4.5h with zero log pushes). User approved running ALL FOUR extract cells
    plus both generations locally, making the G1 instrument symmetric: both
    arms' union (18,496 rows) and holdout (400 rows) surfaces plus both
    generations through the identical local lane. G2 panels ran in the
    pinned docker image that produced the reference. The tarball fix for the
    HF 10k files-per-directory limit is committed at df66b9dc.
- id: 002-result
  at: '2026-07-05T11:55:00Z'
  kind: result
  title: 'Amendment AI scored: G0 PASS both arms, G1 FAIL significantly inverted (-17.0pt), G2 FAIL both arms'
  summary: >-
    G0: fresh per-arm probes OOF AUROC 0.9948/0.9946 on 18,475 union rows;
    both arms full 2,934 steps, no halts. G1: TRUE congruence 59.75 percent
    vs PERMUTED 76.75, differential -17.0pt, 10k paired bootstrap CI [-21.5,
    -12.5] excluding zero on the wrong side (gate needed >= +10pt); every
    descriptive stratum negative. G2 vs pinned GRPO-v2 reference: abstain
    preserved (+0.49pt) but answer-when-answerable +37.9 and correctness
    among answered -20.2 (PERMUTED descriptive trio 89.73/86.22/27.99).
    Composition note recorded, not scored: 387/400 holdout rows are D-over,
    so congruence tracks answer rate on this pool; TRUE refuses rows its own
    readout misreads as answerable.
- id: 003-decision
  at: '2026-07-05T12:05:00Z'
  kind: decision
  title: 'User adjudicates NULL; seeds backlogged; pivot to radial steering ON the AI-TRUE checkpoint, locally'
  summary: >-
    User: the result is trusted as-is (aligns with M/N/R/AA/AB and AH); seed
    replication goes to backlog. Verdict merged via PR #207 (branch first
    synced with main; paper3/paper4 conflicts resolved to main's copies).
    Scoreboard TIE/TIE - both parties predicted TRUE wins; tally user 3 -
    orchestrator 2 - ties 2. FalseQA-bearing staging dataset repo deleted
    per pre-approval; adapter/base staging repos kept private. AL will run
    on the TRUE checkpoint (not GRPO-v2), preceded by a characterization
    pass, because the user wants its internals inspected against other
    checkpoints anyway; work stays on the local GPU for now.
- id: 004-result
  at: '2026-07-05T12:25:00Z'
  kind: result
  title: 'Three-way internals characterization: readout untouched (transfer ~1.0), axis rotation generic not sensor-specific, drift ~98 percent off-axis'
  summary: >-
    amendment_al_prep_true_internals_cpu.py on the identical 18,496-row
    union pre-gen surface (clean-SFT base all-layer refit surface vs TRUE vs
    PERMUTED verdict extracts, L20/24/28). (1) Readout strength identical
    everywhere (OOF AUROC 0.992-0.995); base sensor reads TRUE states cold
    at 0.9993; all cross-pairings >= 0.9956. (2) Axis rotation from base is
    the same for both arms (L24 cos 0.835 TRUE vs 0.827 PERMUTED) - generic
    GRPO drift, not sensor sculpting. (3) States moved 18-20 percent of
    state norm (control moved MORE), but only ~2 percent of displacement
    lies along the readout axis; one sensor-specific signature: TRUE pushes
    unknown rows toward the unanswerable pole (-0.124) where the control
    pushes them answerable-ward (+0.022). Report:
    analysis/amendment_al_prep/true_internals_report.json (untracked).
- id: 005-result
  at: '2026-07-05T12:40:00Z'
  kind: result
  title: 'Drift decomposition: commitment is the most-moved named axis (label-signed in BOTH arms); caution reshaping is generic; the dominant drift directions are label-organized but unnamed'
  summary: >-
    amendment_al_prep_drift_decomposition_cpu.py projects dh_true,
    dh_permuted, and their difference dd (sensor-specific displacement) onto
    a near-orthogonal L24 bank (answerability from the base union probe;
    caution = refuse-vs-answer and commitment = confab-vs-refuse residualised
    vs caution, both fit on the cached AH A0 GRPO-v2 surface; pairwise cos
    <= 0.03). The bank captures only 2.6-3.8 percent of mean drift. Named-
    axis movements: commitment moved most and is label-signed in BOTH arms
    (TRUE known +0.74 / unknown -0.83; PERMUTED +0.88 / -0.63); caution
    reshaping (less on knowns, more on unknowns) is shared drift, NOT
    sensor-specific (dd caution ~-0.04). The sensor-specific dd is a global
    hold-back shift: anti-commitment (-0.15, strongest on unknowns -0.20)
    plus toward-unanswerable (-0.11) on every stratum. dd's top PCA
    components correlate with gold label (up to |0.46|) yet are nearly
    orthogonal to ALL named axes (cos <= 0.1): the sensor reward built or
    recruited label-organized directions the program has not yet named -
    candidate new axes for MI follow-up. Doubt/caution_perp are L35-only
    artifacts and could not join the bank (arm extracts carry L20/24/28);
    close by adding upper layers to the next extraction cell. Report:
    analysis/amendment_al_prep/drift_decomposition_report.json (untracked).
- id: 006-launch
  at: '2026-07-05T12:20:00Z'
  kind: launch
  title: 'GRPO-v2 union extraction launched locally (user-approved) for the four-way comparison'
  summary: >-
    amendment_ai_verdict_extract_gen.py --stage extract --surface union with
    the GRPO-v2 adapter (schema_clean_sft_grpo_v2_seed1_full/20260624_095831/
    final_model) on the merged clean-SFT base, out to
    analysis/amendment_al_prep/grpo_v2_extract_union/data. Adds the
    deployment checkpoint's drift on the same pool; both characterization
    scripts then extend to the four-way (drift script takes --grpo-dir).
- id: 008-result
  at: '2026-07-05T13:30:00Z'
  kind: result
  title: 'Four-way decomposition CORRECTS the generic-drift reading: label-signed caution/commitment reshaping is PAR-curriculum drift, absent in GRPO-v2'
  summary: >-
    With the GRPO-v2 union extraction added (18,496 rows, local GPU,
    user-approved), the deployment checkpoint's drift looks nothing like the
    PAR arms: smaller (norm 7.1 vs 10.9/12.1), bank fraction 1.8 percent,
    commitment known -0.15 / unknown +0.03 (opposite sign pattern, near
    zero), caution uniformly slightly UP on both classes (+0.10/+0.06,
    matching its over-refusal profile), and PC1 essentially label-agnostic
    (corr_label 0.06 vs 0.76 TRUE / 0.63 PERMUTED). So the label-signed
    caution/commitment reshaping in checkpoint 005 is NOT generic GRPO
    drift: it is shared by the two PAR arms because both trained on the
    same union pool + reward scaffold (even a permuted probe signal leaves
    pool exposure organizing drift by label). Revised attribution:
    label-signed epistemic reshaping = PAR curriculum; hold-back
    (anti-commitment, toward-unanswerable) = the sensor signal
    specifically; diffuse label-agnostic drift = GRPO generally. Report:
    analysis/amendment_al_prep/drift_decomposition_4way_report.json
    (untracked).
- id: 009-launch
  at: '2026-07-05T14:05:00Z'
  kind: launch
  title: 'RunPod lane first paid launch: TRUE A0-surface cell live on an RTX 3090 (pod 58evmk39j8odgx)'
  summary: >-
    User added RUNPOD_API_KEY (test key, rotates with HF) and directed RTX
    3090 community for local-setup parity. Cell = runpod_al_true_a0.sh at
    pinned sha c2699603: greedy generation (raw answer_text, graded
    locally) + full-stack L0..L36 pre-gen extraction on the 1,662-row A0
    pool with the TRUE LoRA, uploading to the new PRIVATE staging repo
    professorsynapse/eh-al-prep-staging (pool is KUQ/SelfAware/TriviaQA/
    PopQA - no FalseQA). Est ~2h / ~$0.60, 180-min timeout,
    terminate-in-finally. This is the deliberate smoke of the workload
    class that died on HF Jobs networking.
- id: 007-checkpoint
  at: '2026-07-05T12:45:00Z'
  kind: checkpoint
  title: 'Infra: RunPod one-shot job lane in Synaptic-Tuner; research repo keeps zero RunPod code'
  summary: >-
    User-directed placement: the generic pod runner lives inside the tuner
    fine-tuning skill following the HF pattern (Synaptic-Tuner PRs #125 +
    #126: .skills/fine-tuning/scripts/runpod_run_job.py + reference/
    runpod-jobs.md, mirrors synced); research-repo submodule repointed via
    PR #206. Same pinned Unsloth image and terminate-in-finally lifecycle
    as the training backend; wrapper uploads its own outputs. Blocked on
    RUNPOD_API_KEY in .env (user action), then a small paid smoke.
    Remaining AL-prep GPU cell to spec: AH-A0-style surface on the TRUE
    checkpoint (1,662 rows, generations + pre-gen states incl. L32-36 for
    the doubt axis), which turns the PR #204 ceiling table into
    TRUE-specific AL gate thresholds.
---

# Session 0038 — Amendment AI NULL verdict; AL prep opens on the TRUE checkpoint

Arc: cloud-lane failure cascade resolved by an all-local symmetric verdict
instrument; Amendment AI scored and adjudicated NULL with an inverted G1;
the use-the-signal program closes at five null channels; AL prep begins on
the TRUE checkpoint with two CPU characterization instruments whose first
results locate the training change almost entirely OFF the named epistemic
axes, with commitment the most-moved named direction and the dominant
sensor-specific movement in label-organized but unnamed territory.
