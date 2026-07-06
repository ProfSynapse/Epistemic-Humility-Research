---
schema_version: research-session/v1
session_id: '0038'
title: Amendment AI NULL verdict (G1 inverted) and AL prep on the TRUE checkpoint (internals characterization + drift decomposition)
status: active
created_at: '2026-07-05T09:00:00Z'
updated_at: '2026-07-05T19:45:00Z'
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
- id: 010-checkpoint
  at: '2026-07-05T14:55:00Z'
  kind: checkpoint
  title: 'RunPod boot failures diagnosed (no min_download floor + launcher boot-detection bug); prioritized path reassigned to local GPU, RunPod demoted to lane-debug'
  summary: >-
    Pods r1 (58evmk39j8odgx) and r2 (luiec5fy5ob38e) both stalled forever
    pulling the ~20GB pinned unsloth image on community RTX 3090 hosts
    (desiredStatus RUNNING, uptime 0s, no log push; a documented RunPod
    community-cloud failure mode). Two root causes: (1) the launcher never
    set create_pod min_download/min_upload, so slow-network hosts win the
    bid; (2) launcher counted status==RUNNING with an empty-uptime runtime
    dict as booted, disarming the 600s boot timeout, so a stalled pull
    polls to the 180-min cap (r1's launcher also died at compaction,
    skipping terminate-in-finally - the orphan was killed manually).
    Launcher patched (scratchpad test copy, to be PR'd into the tuner
    skill after a green run): min_download 700 / min_upload 200 Mbps
    floors, booted requires uptimeInSeconds > 0, boot timeout 900s.
    User-directed lane split: local 3090 carries the prioritized AL path
    (PERMUTED A0 cell running, TRUE A0 cell chained behind it, identical
    two-stage runs, outputs under analysis/amendment_al_prep/); RunPod r3
    (pod zdpe0yxma9gjl8, user-approved) reruns the TRUE cell as a
    non-blocking lane test that doubles as a cross-lane parity check
    against the local TRUE surface. Modal lane paused by the user (token
    pair in .env rejected by the API as nonexistent; needs a fresh
    dashboard token).
- id: 011-result
  at: '2026-07-05T15:55:00Z'
  kind: result
  title: 'Local A0 cells complete + graded; L35 doubt-axis check lands; RunPod boot failure survives every isolation probe including SECURE cloud'
  summary: >-
    Prioritized path: both local A0 cells finished (PERMUTED then TRUE,
    chained; 1,662 rows each, greedy gen + full-stack L0..L36 pre-gen
    extraction, integrity-verified). AH-lineage grading
    (amendment_al_prep_grade_a0_generations.py): TRUE answers 64.8% of
    answerables at 42.9% accuracy-among-graded and confabulates 8.7% of
    unanswerables; PERMUTED 75.9% / 38.2% / 15.2% - the sensor arm's
    hold-back trades ~11pt answering for ~halved confabulation. Doubt-axis
    check (amendment_al_prep_doubt_axis_check.py): arm-local L35 doubt
    axis reads answerable-vs-unanswerable at 0.90 AUROC and, within
    unanswerables, confab-vs-refused at 0.84 (confabs sit on the
    reads-as-known side - the radial/gated intervention has signal);
    local caution reads refusal 0.93. grpo_v2 reference axes transfer
    weakly (0.68/0.65, direction cos ~0.17/0.05; cross-surface AND
    cross-checkpoint - refit per checkpoint confirmed). TRUE and PERMUTED
    local axes are near-identical (cos 0.99/0.97/0.95): the reward
    mapping does not rotate the readable geometry. Row-aligned TRUE-PERM
    drift peaks mid-network (L19-23, rel 0.12-0.13, echoing the 008
    4-way decomposition) and at L35 is mostly OFF-axis (variance fraction
    2-5%; mean drift cos -0.26 with doubt / +0.27 with caution, signs
    matching the behavioral hold-back). RunPod lane: probes 2/3 (REST
    dockerEntrypoint override; official cached runpod/pytorch image), a
    4-min sleep probe, and probe C on SECURE cloud ALL fail identically
    (RUNNING, uptime 0, 900s timeout, self-terminated) - community-pool,
    image-pull, entrypoint-crash-loop, and fast-exit explanations
    eliminated; every dead pod shares RTX 3090 + dockerEntrypoint
    override as the last untested variables. Launcher rewritten on the
    REST API along the way (JSON body kills the SDK's unescaped
    dockerArgs GraphQL bug; allowedCudaVersions enum caps at 13.0; no
    log API exists - uptime is the only boot signal). Next discriminator
    (needs approval): one non-3090 SECURE probe and/or one probe without
    the entrypoint override.
- id: 012-result
  at: '2026-07-05T17:10:00Z'
  kind: result
  title: 'RunPod exonerated: the entire 10-pod boot-failure saga was launcher instrumentation; fixed probe boots in under 2 minutes; TRUE A0 parity cell relaunched (r4)'
  summary: >-
    CORRECTS the failure attribution in checkpoints 010-011. The approved
    discriminator batch (probe D SECURE A5000 with entrypoint override,
    probe E SECURE 3090 official image without it) "failed" identically,
    which eliminated the last two platform hypotheses and forced an audit
    of the sensor itself: the REST /pods response carries NO uptime field
    at all (docs confirm; only desiredStatus/lastStartedAt), so the
    launcher's uptimeSeconds boot check read every pod - healthy or not -
    as never-booted and killed it at the 900s timeout. All six REST-era
    "boot failures" (probes 2/3, sleep probe, C, D, E) were self-inflicted;
    the GraphQL-era failures have separate mundane explanations (r1/r2:
    20GB image pull with no min-download filter; probe A: image ENTRYPOINT
    crash-looping on command-as-args). Fix: create/terminate stay on REST
    (JSON body + dockerEntrypoint override), boot polling moves to GraphQL
    runtime.uptimeInSeconds - which needs the SDK-style api_key query
    param (Bearer header alone 403s) AND a custom User-Agent (Cloudflare
    403s default Python-urllib). Verification (user-approved): fixed probe
    on a community 3090 booted in <2 min (PROBE BOOT OK, uptime 15s,
    self-terminated); the chained TRUE A0 parity cell relaunched as r4
    (pod u0bi6ss3wdxs7n, $0.22/hr, 180-min cap), uploading to the private
    staging repo for the cross-lane parity check against the local TRUE
    surface. Methodological lesson recorded: hypotheses were "eliminated"
    for hours through a detector that could not fire; verify the failure
    sensor against a known-good case before indicting the platform.
    Launcher PR into the tuner skill proceeds after r4 completes
    end-to-end.
- id: 013-result
  at: '2026-07-05T19:45:00Z'
  kind: result
  title: 'Confab cloud characterized; "commitment" renamed confabulation propensity on scope-check evidence; ungated ceiling quantified (clean channel, modest reach, only honest zero-collateral point)'
  summary: >-
    Three CPU instruments closed the AL control-law design loop on the
    TRUE surface. (1) familiarity_vs_knowing: the blind-spot confabs
    (user-coined "confab cloud") are boundary-elevated without knowledge
    (doubt means: correct 2.22 / wrong 1.55 / confab 0.34 / refused
    -0.35; actually-knowing axis reads confabs at refusal level, 0.46);
    familiarity is flat (0.51 alone; internal-direction residualization
    moves 0.84 to only 0.83) though raw text-surface features soak part
    of the elevation (0.84 to 0.68-0.70) - refines, does not contradict,
    the 0037 matched-doubt familiarity result. (2) commitment_scope_check
    (user prompted the naming question): the fabricate-vs-refuse
    direction is confabulation-SPECIFIC, not generic answer-commitment -
    negative alignment with the answer-vs-refuse direction (cos -0.35),
    chance transfer at matched caution (0.46/0.51), raw transfer inverted
    (0.30). Renamed confabulation-propensity direction; KG ingest
    committed (3cfb56d9): internal evidence note + 2 terms (confab-cloud,
    confabulation-propensity-direction) + 4 mechanisms + reciprocal edges
    into the 0037 atoms. (3) Ceiling sims: a clean-cell mean-diff gate
    (correct-vs-confab AUROC 0.926) reaches FEWER confabs than the
    logistic gate at 1 collateral (31 vs 46, permute-gate p=1.0 both) -
    the blind spot is tail overlap, robust to gate construction; the
    UNGATED anti-propensity law (agent-built, d999c10a) is
    permutation-real at every point (p=0.005) but modest: balanced 30/116
    at 1 collateral (ties meandiff-gated, loses to logistic-gated 46),
    and its distinguishing offer is the only honest zero-collateral point
    (5/116; gated "zero-collateral" reach was gate-driven and
    chance-indistinguishable). One high-propensity correct answer (prop
    2.50) caps the zero-collateral region. Aim-small: conservative
    infeasible (half-effect CI floor 0), balanced gates {collateral<=3,
    >=5 confabs killed}. AL design fork now a user decision: honest-floor
    ungated vs max-reach gated-logistic primary. Infra: r4 parity cell
    died on a bad host (real signal this time - probe booted 15s);
    launcher gained boot-fail host recycling (max 3); r5 launched
    (user-approved). Modal credentials refreshed by user; smoke + PR of
    fix/modal-remote-shared-import delegated to a background agent.
    User feedback pinned to memory: delegate more, protect main-loop
    context.
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
