---
schema_version: research-session/v1
session_id: 20260708T164625Z-paper-5-j-space-hardening
title: Paper 5 J-space hardening
status: active
created_at: '2026-07-08T16:46:25Z'
updated_at: '2026-07-14T22:40:03Z'
track: research
phase: phase1
question: Which registered follow-up experiments harden the Paper 5 actuation thesis,
  starting with a fresh Qwen3-4B J-space layer-site replication?
tags:
- paper5
- j-space
- actuation
run_ids:
- rr3-pipeline-20260714b
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Paper 5 draft merged to main; same-model J-space layer-site replication
    being registered before cross-family escalation.
  changed_by_session: Created the fresh-pool replication amendment scaffold and row-mining/extraction/contrast
    instrument.
checkpoints:
- id: 011-decision
  at: '2026-07-09T13:54:25Z'
  kind: decision
  title: Decision
  summary: 'Replication signed and launched; cross-family queued with dedup constraint.
    User prediction recorded (full replication, +18-25pp) alongside orchestrator (holds-but-shrinks,
    +10-18pp); j-space-layer-contrast-replication signed (826d9a1c on agent/jspace-full-run)
    and the full 4-layer contrast launched on the local 3090. Scaffolded j-space-cross-family-layer-contrast
    (d2134050 on exp/j-space-cross-family-layer-contrast) using Amendment Z''s family
    panel. Worktree audit found the signed doubt-snap-cross-family-confirmatory mid-run
    on Modal over an overlapping panel: to avoid duplicating its per-family FIT pipeline,
    the cross-family layer contrast HOLDS unsigned until that run resolves and is
    revised to consume its pools/splits/late-site artifacts. Also inherited its pre-outcome
    loader finding by substituting Mistral-7B-Instruct-v0.3 for Amendment Z''s Ministral-3-3B
    (Mistral3ForConditionalGeneration is not a causal-LM write substrate). Open decision
    points for sign time: G3 late-reference floor 0.40/0.30 is a draft guess; multimodal
    loader paths and per-family EOS lists unverified.'
  evidence:
  - experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md
  - /home/profsynapse/code/ehr-worktrees/jspace-cross-family/experiments/j-space-cross-family-layer-contrast/AMENDMENT.md
  - /home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 012-result
  at: '2026-07-09T17:28:55Z'
  kind: result
  title: Result
  summary: 'Replication resolved: registered G1 FAIL (null-result), PR #263. Full
    run completed flawlessly on the 3090 (exact readback, zero collapse, all 2,263
    rows x 4 arms). Best mid-band hs29 99.67% vs hs34 94.12% = +5.6pp, under the 10pp
    bar; G2/G3 passed; both scoreboard predictions wrong. Post-run red-team reproduced
    every number and corrected the mechanism story before the Outcome was written:
    ceiling effect with a structural cause (fresh confabs single-source kuq_ku_unknown_x,
    the two harder predecessor sources absent from the candidate universe), so this
    is a narrower-distribution replication; direction survives with CI separation
    at hs23/hs29 (not hs26); hs34 deficit is write-effectiveness not gate-transfer;
    hs29 has the worst known-correct cost. Carried forward: Paper 5 pool-sensitivity
    caveat; cross-family experiment needs a ceiling-robust G1 (CI separation + failure-ratio)
    and multi-source confab mining before sign. Infra shipped same session: tuner
    RunLog (Synaptic-Tuner PR #141) + consumption/skill invariant (PR #262) after
    catching the buffered-run risk mid-flight; per-row persistence gap in this run
    is the motivating case.'
  evidence:
  - experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md
  - https://github.com/ProfSynapse/Epistemic-Humility-Research/pull/263
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 013-interpretation
  at: '2026-07-09T19:21:21Z'
  kind: interpretation
  title: Interpretation
  summary: 'Qwen3.5 doubt-snap dose-fit failure audited: overdose collapse, NOT a
    family null and NOT an inert write. Opus audit of the Modal artifacts falsified
    the hook-path/inert-write hypothesis (readback write_ok=true, commanded ~100 realized
    99.96-100.04, layer 29 correctly derived from nested text_config) and the grader/render
    hypothesis (baseline well-formed 0.995/0.987). Root cause for BOTH cells: the
    registered absolute dose grid {100,150,200,250} is mis-scaled to Qwen3.5 residual
    geometry. Qwen3.5-4B sigma_c=2.80 (4.7x smaller than the working Qwen3-4B reference)
    puts even dose 100 at 38-sigma: 854/854 fired confabs degenerate (repeating I-dont-know
    token to cap). Qwen3.5-9B shows textbook dose-graded collapse: refused 18->363->886
    across 100->150->200 while well_formed falls 886->503->2 (JSON colon corrupts
    before content); peak clean 5.1% at dose 150; its coherent window sits below/between
    the grid. Key science: sigma-distance is NOT portable across models (9B at 15.8
    sigma matched the reference''s working point and still collapsed); usable windows
    are absolute and model-specific, consistent with the J-space dose-calibration
    prior. Disposition: instrument failure, NOT-RUN candidates, must not be reported
    as doubt-snap-null-on-Qwen3.5 (9B refuses 97% of confabs on command). Honest limit:
    no proof a window clearing 60%/10% exists; grid never sampled below 100. Gap found:
    Modal rows carry no per-row readback field (smoke-only), unlike the local pipeline.
    Proposed (NOT run): finer low grids (4B ~10-75, 9B ~60-140) reusing volume artifacts,
    ~1-2 GPU-h ~$1-3/cell, but this changes the LOCKED grid and needs a signed revision
    -- lifted to user.'
  evidence:
  - /home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/analysis/from_modal/qwen35_4b/committed/dose_fit.json
  - /home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/analysis/from_modal/qwen35_9b/committed/build_manifest.json
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 014-amendment
  at: '2026-07-09T20:59:59Z'
  kind: amendment
  title: Qwen3.5 dose-grid recalibration registered + relaunch dispatched
  summary: 'Registered the pre-outcome Qwen3.5 dose-grid recalibration on doubt-snap-cross-family
    (commit 8aa1dc02 on exp/doubt-snap-cross-family): per-cell FIT grids 4B {10,20,30,40,50,60,75}
    / 9B {60,80,100,120,140}, selection rule and thresholds unchanged, A10G operational
    change folded in. User approved the paid FIT-sweep-only Modal relaunch (~$1-3/cell);
    relaunch executor dispatched to verify volume artifact reuse and launch both cells
    at batch 1. Rep-2 multisource scaffold completed: 221 fresh confabs (139/6/76
    across three sources), G0 mining floors pass, 8-row smoke green with RunLog per-row
    persistence confirmed; awaiting rebase onto main + gate text + predictions + sign.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Report relaunch app IDs; then rep-2 sign flow (rebase, gate text to user, both
    predictions, sign, launch on 3090).
  signals: {}
- id: 015-result
  at: '2026-07-10T01:25:26Z'
  kind: result
  title: 'Rep-2 multi-source layer contrast: FULL PASS, resolved, PR #264'
  summary: 'Rep-2 resolved FULL PASS on the multi-source pool: hs29 92.76% vs hs34
    73.76% (+19.0pp), paired McNemar 42:0 discordants p=4.5e-13, G2'' +1.43pp, G3''
    interpretable at 73.76%. Red-team reproduced every number from per-row RunLog;
    lead re-derived the paired table; two disclosures registered (hs29 absolute cost
    doubling; 179 distinct normalized questions among 221 rows, verdict invariant).
    Both scoreboard predictions correct. Pairs with rep-1 as the pool-sensitivity
    story: magnitude unidentifiable near ceiling, replicates off-ceiling with the
    same frozen instrument. PR #264 open. Qwen3.5 Modal dose sweeps still in flight.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'Merge PR #264 after user review; adjudicate Qwen3.5 dose selections when Modal
    reports; then revise cross-family layer contrast to consume validated ceiling-robust
    gates.'
  signals: {}
- id: 016-result
  at: '2026-07-10T07:56:02Z'
  kind: result
  title: 'Qwen3.5 recalibrated sweeps: both cells G0 null, family-level no-window
    finding'
  summary: 'Both recalibrated Qwen3.5 FIT dose sweeps committed selected_dose null.
    4B: coherent tighten peaks ~33% at dose 40 then JSON-corruption collapse (well-formed
    90%->55%->3% across 40/50/60); 9B: peaks ~6% near 140-150 before the 200 cliff.
    Well-characterized no-window nulls, not grid artifacts: the doubt-gated caution
    snap does not transfer to Qwen3.5 at registered thresholds (vs 73.5% held-out
    on Qwen3-4B). Both cells ineligible-before-held-out for the cross-family denominator.
    NOTEBOOK entry committed on exp/doubt-snap-cross-family.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Present resolve-time adjudication options for the cross-family panel eligibility
    arithmetic to the user; remaining panel cells proceed.
  signals: {}
- id: 017-decision
  at: '2026-07-10T10:52:21Z'
  kind: decision
  title: 'Qwen3.5 nulls decomposed: regulation transfers, format breaks; 4B-local
    mid-band next'
  summary: 'Row-level decomposition of both Qwen3.5 null cells reframed the finding:
    9B doubt-write actuates stated-confidence refusal on 886/912 fired confabs at
    dose 200 (format-agnostic ''refused'' flag) but strictly entangled with JSON corruption
    (well-formed 2/912); 4B peaks at ~39% refusal even format-free before total degeneration.
    User adjudication: strict JSON was partly a parseability holdover; the honest
    framing is ''regulation works, format breaks'' for 9B, weak-actuation for 4B.
    Verified the old forced-fill issue is triple-guarded now (min_new_tokens=1 + EOS,
    baselines natural-stop 99%/98% at 69/102 avg tokens, clean_tighten requires natural
    stop). Flag quirk noted: 4B dose_50 semantic_refuse (142) > refused (115). DECISIONS:
    (1) anchor-placement audit (read-only, free) is the last unchecked harness surface;
    (2) refusal/coherence decomposed readout gets governed provenance inside (3):
    a new exploratory amendment testing whether a J-space mid-band write site on Qwen3.5-4B
    decouples refusal from corruption, run LOCALLY on the 3090 per user (stronger
    finding if the weakest cell rescues; free lane). Requires Qwen3.5-4B J-lens profile
    (band is model-specific), fresh mid-band captures/fits from doubt-snap FIT rows,
    small dose ladder with collapse diagnostics.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Dispatch anchor audit + scaffold qwen35-4b-midband-doubt-snap amendment in a new
    worktree (draft, profile as pre-sign prep, no sign without user).
  signals: {}
- id: 018-infrastructure
  at: '2026-07-10T11:02:40Z'
  kind: infrastructure
  title: 'Tuner lines reunified (PR #142); doubt-snap branch merged (PR #265)'
  summary: 'Merging the doubt-snap branch surfaced a diverged submodule pin: exp branch
    at 9a97540 (batch verbs, HF-token loaders, batched steer) vs main at cd30d482
    (RunLog, redaction, dose calibration), neither containing the other. Resolved
    by merging the tuner lines: Synaptic-Tuner PR #142 (one additive conflict in MechInterp/cli.py,
    both helper blocks kept; 206/206 tests pass) -> tuner main 86b134c. Repo submodule
    repointed to 86b134c in the merge commit; PR #265 (Qwen3.5 dose recalibration
    + characterized no-window nulls + Modal durability/operational fixes) merged to
    main. All future pins get RunLog + batch/steer verbs together. User approved the
    tuner merge explicitly after a classifier lift.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'PR #264 (rep-2 full pass) still open awaiting user review. Anchor audit + mid-band
    scaffold agents in flight.'
  signals: {}
- id: 019-decision
  at: '2026-07-10T12:57:38Z'
  kind: decision
  title: 'Standing directive: local GPU runs move to pinned Docker images'
  summary: 'User directive (2026-07-10): moving forward all local 3090 experiment
    runs use the Docker method, never bare shared conda envs. Trigger: unsloth_env
    silently aged out of model_type qwen3_5 (transformers too old), forcing a documented
    mid-experiment env hop to base conda; file instruments are sha256-pinned in experiment.yaml
    but the runtime was not, an asymmetry in the provenance story; Modal lane already
    containerized. Implementation queued: (1) generic mechinterp runner image in synaptic-tuner
    (CUDA + torch + pinned transformers + flash-linear-attention, digest printed at
    run start) via tuner branch+PR; (2) mechinterp-cells skill invariant in canonical
    .skills/: local GPU runs execute in the pinned image and experiments record the
    image digest in instrument.pins; delegation prompts restate it. Exception honored
    once: qwen35-4b-midband-doubt-snap finishes on its documented deviation; containers
    bind at the next experiment boundary.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Builder dispatched for the tuner Dockerfile PR + skill-invariant PR.
  signals: {}
- id: 020-checkpoint
  at: '2026-07-10T14:15:52Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Midband Stage A+B lead spot-check PASSED (build_manifest per-layer AUC/tau/sigma_c
    match report; reused_rows_manifest strictly ID-only; provenance pins verified).
    RunLog deviation for Stage A adjudicated ACCEPTABLE (per-layer JSON flush provides
    the crash-resume property at the loop''s natural granularity); ruling to be recorded
    in experiment NOTEBOOK by the Stage C builder. Fresh stagec-builder agent dispatched
    to write and smoke run_dose_ladder.py (RunLog per-row, registered decomposed readouts,
    grader mirrored verbatim from doubt-snap cross-family) before sign. Docker lane
    closed out: mechinterp-runner:local built green (numpy 2.2.6 / sklearn 1.7.2 Python-3.10
    caps), lead GPU smoke in-container passed (CUDA on 3090, qwen3_5 config parses,
    provenance JSON emitted); both branches pushed and PRs opened UNMERGED for user
    review: Synaptic-Tuner #143, EHR #266.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 021-checkpoint
  at: '2026-07-10T14:46:48Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'User approved and lead merged all three open PRs: Synaptic-Tuner #143
    (pinned mechinterp runner image, CUDA 12.8.1/torch 2.9.1/transformers 5.12.1),
    EHR #266 (Docker local-lane skill invariant), EHR #264 (rep-2 j-space layer-contrast
    FULL PASS evidence). Repo main now at 618b62bc; tuner submodule pin unchanged
    at 86b134c (no pin bump needed; future experiments adopt the runner image from
    tuner main). Docker directive is now fully on the record in skills; the qwen35-4b-midband
    cell remains the one honored env-deviation exception.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 022-checkpoint
  at: '2026-07-10T14:58:11Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'qwen35-4b-midband-doubt-snap SIGNED after Stage C builder delivered run_dose_ladder.py
    (smoke PASS: readback within 0.3%, natural stop, RunLog resume verified zero-regen;
    3 registered arms x 4 layers x 7 doses = 84 cells + shared baseline, ~74,750 generations).
    Predictions registered pre-outcome: user G1-passes (decouples), orchestrator G1-passes
    (hs23, 6-12 sigma). Grids/floors locked (refused>=60% AND well_formed>=80%, known
    false-refusal<=10%). Sign gap caught and fixed: bin/exp sign pinned only the scaffold''s
    5 instrument files; the 3 Stage C modules added to modules+pins by hand (sha256)
    pre-launch, recorded in experiment NOTEBOOK. Launch plan user-approved: batch
    probe (16/32 with semantic parity vs 8) then full ladder on the free 3090; dispatched
    to stagec-builder. Also this segment: user approved and lead merged tuner #143,
    EHR #266, EHR #264.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 023-checkpoint
  at: '2026-07-10T15:24:06Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Stage C batch probe + launch (stagec-builder report, lead-verified process
    live): Qwen3.5 batch-composition non-determinism CONFIRMED on the local 3090,
    not just Modal A100s -- at bs=16 and bs=32 vs the bs=8 reference (n=30 rows, hs23,
    dose 8 sigma), most divergence was wording drift but one row (kuq_unknowns_all:1041,
    gated arm) categorically flipped refused=True/clean_tighten=True at bs=8 to a
    substantive answer at BOTH 16 and 32, i.e. batch size flips primary G1 gate metrics.
    Fallback rule applied: full ladder launched at batch 8, 2026-07-10 11:20 local,
    harness-tracked, pinned-file hashes verified byte-identical pre-launch, probe
    scratch cleaned. Revised runtime ~48-55 h (74,753 generations; measured ~1.7-3.5
    s/row by arm). Run order: shared baseline then per layer (20->23->26->30) gated+permuted_gate
    then random_direction, all doses per RunLog file; resumable per dose|row key.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 014-checkpoint
  at: '2026-07-10T19:19:39Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'PR #258 (experiment provenance reorganization) MERGED after full audit
    + remediation arc. Fable-tier audit verified: all 40 legacy amendments migrated
    with verdicts/gates/numbers byte-preserved, 45/45 run records archived, no new
    data exposure, nothing stranded on the Windows-side worktree (identical to PR
    head, clean). Blocking findings fixed by remediation: 7+44 dangling evidence pointers
    in governed docs corrected against the audit census, 23 stale historical pins
    re-pinned (+3 more surfaced by the main merge) with NOTEBOOK provenance entries,
    exp validate extended to gate historical-status pin drift, main merged with 5
    conflicts resolved (mechinterp SKILL.md restructure kept both invariant sets;
    session notes renamed to timestamped scheme with checkpoints preserved and renumbered).
    Post-merge: validate OK (60 experiments) on main. Session-note tooling now uses
    the timestamped path (this checkpoint is the first at the new path).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 015-checkpoint
  at: '2026-07-10T21:49:59Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Paper 4 revision arc executed and merged: reviewer memo recovered from
    agent transcript and committed (docs/review/paper4-two-signal-readout-review-2026-07-10.md);
    PI approved full plan incl. veto requalification + logprob baseline. paper4-revisor
    (fable) executed all 8 memo items, lead-verified against AM/AP/rep2 amendment
    docs, merged dcfa6634. Intro citation anchors added f9da0ba8. PRs merged: #269
    (Amendment Z Z-G3 gate-wording erratum, notebook-tier), #270 (dial logprob baseline
    NOT computable from cache: extraction never recorded logits; teacher-forced CPU/GPU
    re-forward deferred until midband ladder frees the 3090). VOICE.md gained binding
    ''Synthesis, not journey'' section (PI directive): superseded numbers never on
    the page, predictions/gate-misses as compact registered facts, process narration
    only in AI-workflow methods. Synthesis pass dispatched to paper4-revisor: remove
    0.980 veto number entirely (confounded per AM/AP; honest ~0.74 controlled core
    is the finding), de-narrate confound-hunt arcs. Queued for same pass: related-work
    readability (PI reading feedback: section 2 blocks open with apparatus not question,
    and argue our +0.065 inside related work; fix = plain-language question openers,
    our numbers out of section 2). Midband ladder healthy: hs20 arms done through
    permuted_gate, into gated dose_12, GPU 55%.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 016-checkpoint
  at: '2026-07-10T22:28:01Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Paper 4 editorial arc continued through three more PI-directed passes,
    all lead-verified and merged: (1) synthesis pass (0.980 removed from all sites
    incl. a rhetorical-foil survivor the lead caught; 4.4 rewritten as decomposition
    statement; U overshoot story dissolved, controlled core sits inside registered
    band; Figure 5 rebuilt from generator; lead adjudication 91722d5a scoped 4.3 decomposition
    attribution to raw base as explicit inference). (2) related-work pass (section
    2 question-first rewrite, our numbers out of related work, steering block reduced
    to one scoping sentence with substance consolidated in section 6; merged 95bff4ae).
    (3) self-containment + headings pass (body prose freed of amendment codenames/doc
    filenames/slugs/PR numbers/repo paths, provenance consolidated to Appendix A with
    7 new verified rows; ~25 bold run-ins converted to real subheadings; lead fix
    959603d5 promoted section 3 setup blocks to ###; merged e0c833d9). VOICE.md gained
    three new binding sections this arc: Synthesis-not-journey, External-facing self-containment,
    real-headings structure habit. TODO backlog: CD (correctness-direction rotation
    tracking, upgrades dial cold-transfer inference to measurement) + LP (logprob
    re-forward), both gated on midband ladder freeing 3090. Forward note: companion-paper
    reference should switch to paper 3''s own identifier when it exists. Revisor on
    standby for further PI reading feedback.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 017-checkpoint
  at: '2026-07-10T23:54:42Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'H9 feasibility adjudicated: NOT computable from cache (AL fit on full
    1,662-row surface, no held-out split; in-cell OOF 0.6802 recorded as gate-setting
    prior); memo committed e1ec09bb, H9 backlog row now CPU+GPU, scout dispatched
    on held-out candidate-list recoverability (union 18,496 minus fit 1,662). Answered
    PI question on doubt+propensity combination: parallel mirrors (AC doubt, AO propensity,
    AN selector) plus ONE additive two-sensor controller g_i=-a_d*z_d+a_p*z_p in draft
    exp two-signal-caution-regulation-instruct, killed at calibration, collapsed to
    doubt-only gate in tighten; no serial confab-through-doubt routing exists. Worktree/branch
    audit run: two-signal AMENDMENT.md+experiment.yaml were UNTRACKED disk-only, now
    committed+pushed on their branch (was never pushed); Amendment Y-thinking draft
    stranded on amendment-y-thinking-readout branch (absent from main, never migrated);
    AK worktree holds uncommitted ak_stage2 G3 report + row-level pull data; steering-cell
    skill branch never merged (mechinterp-cells likely supersedes); old amendment
    branches (AE/AG/AH/AB/AC/R/Y-base) verified MIGRATED to experiments/ on main,
    stale; jspace replication/localization branches stale (main ahead, resolved).
    Next: PI decision on stranded drafts + stale-branch cleanup sweep.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 018-checkpoint
  at: '2026-07-11T00:31:59Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Editorial + hardening batch progress. Paper 3 anatomy pass verified+merged
    (c2e977b2: doubt=answerability-gate identity, caution trained-only caveat as finding,
    propensity one-line pointer, A3 move-out, self-containment). Paper 2 voice pass
    verified+merged plus 3 lead adjudications (b781f937: abstract KTO seed count corrected
    to two analyzed seeds per amendment_a_selfaware_summary.csv, grammar, ranking-signal
    scoping). Steering-cell salvage merged (PR #271: smoke-first+SHA-pin discipline,
    gate-primitive logic, PEFT/layer-offby-one/ULP gotchas into mechinterp-cells);
    Y-thinking draft archived (5da6587d); both retired branches await explicit PI
    deletion OK. H9 SIGN-OFF: PI prediction recorded = G1 INCONCLUSIVE band (f9e7c995);
    PI approved sign + HF staging + Modal spend cap $15; h9-designer wiring scripts
    + FID smoke (d_raw hard target adjudication confirmed; note designer correctly
    identified AL=radial-anti-propensity-steering, not selected-setpoint-regulator
    which is AN). New backlog row TS: steering-under-thinking cell (does gated caution
    write change the CoT; reuses archived cot_confidence rubric; after H3/H4). PI
    directive: draft H3/H4/H6/TS with placeholders NOW; two designer agents dispatched
    (a: H3 exp/h3-snap-seed-decode-replication + H4 exp/h4-ungated-dose-matched; b:
    H6 exp/h6-genstream-hook-check + TS exp/ts-steering-under-thinking). Ladder: hs20
    gated dose_20 320/882, ~3.8s/row, GPU 26%/9GB/60C, no crashes, ETA ~2 days. Next:
    verify 4 drafts, red-team H9 instrument post-wiring, sign, stage checkpoint, Modal
    launch.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 019-checkpoint
  at: '2026-07-11T03:42:12Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'H9 cloud run arc complete. Attempt 1 reaped (undetached client exit, operator
    error). Attempt 2 crashed at extraction start (ModuleNotFoundError: fresh clone
    lacks the untracked legacy probe tree the local checkout has). Instrument repair
    2 = bin/exp repin FIRST PRODUCTION USE: install legacy-wrapper-tree at experiment/phase1/probe,
    shim renamed AC config (prompt.system verified byte-identical across rename d55b7d26),
    PYTHONPATH, fail-fast import preflight before model download; rehearsed green
    in a clean pinned-commit checkout; commit b4b68ef0. Attempt 3 completed BOTH GPU
    stages (500/500 extract, fidelity spot-check 0.0; 500/500 generate) then crashed
    at harness step 4b reading gen/rows_graded.jsonl where the entry script writes
    gen/rows.jsonl; stage trees lost because checkpoints were top-level-only; app
    stopped to cut retry spend. Repair 3 = filename fix + in-run tree mirroring +
    restore-on-start resume (unit-tested; repin 844f4c7b; commit 58e598c7). Attempt
    4 ran clean end to end: preflight OK, extract OK, generate OK, DONE marker on
    volume. Spend ~2 USD of 15 USD cap. Next: pull ckpt/h9-holdout-r1, run signed
    score_holdout.py, adjudicate locked gates (PI prediction: G1 inconclusive band).
    Durable lesson: CPU smokes never execute the cloud harness post-stage plumbing;
    in-run tree checkpointing caps the cost of such bugs at one stage.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 024-checkpoint
  at: '2026-07-11T10:20:27Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'H9 RESOLVED: INCONCLUSIVE-BY-POWER, PR #273 open. The enlarged read-once
    adjudication on the 750-row draw: the +250 registered enlargement (RNG continuation,
    replay hard-asserted line-identical to the committed 500 manifest, largest-remainder
    allocation 113/69/20/17/12/11/8, 0 near-dups flagged) added ZERO confabulations
    - 4 total in 605 unanswerable rows, 601 honest refusals - so H9-G0 stays unmet
    and per the pre-registered remedy text no further enlargement is permitted; G1
    never read. G2 caution control passed both reads (0.9734/0.9702): pipeline certified,
    confab scarcity is real behavior (AI-TRUE refuses 99.3 percent of held-out unanswerable
    rows vs ~91 expected from fit-surface rates, plus 30/97 knowns). Verdict + scoreboard
    adjudication in AMENDMENT.md section 10 (PI''s INCONCLUSIVE call closest; orchestrator''s
    G0-met call wrong). The repair-3 resume machinery made the enlarged pass cost
    603 GPU-seconds. Total spend ~2 USD of 15. TODO H9 row closed with the follow-up
    note: any future propensity gate needs a surface where the checkpoint actually
    confabulates (weaker checkpoint or adversarial pool), not more rows from this
    one. Paper 5 consequence recorded: the read half of ''reads but does not actuate''
    keeps the in-cell OOF 0.6802 label; no registered held-out number exists. Local
    3090 ladder meanwhile: hs20 complete, hs23 gated mid-run (interim: hs23 notably
    weaker than hs20 - 13/27/36 percent vs 21/46/59 at doses 2/4/6), hs26 pending,
    ~1 day to finish. Remaining follow-ups: KG-ingest of the H9 verdict (librarian,
    post-merge), PR #273 merge, H3/H4/H6/TS wiring.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 025-checkpoint
  at: '2026-07-11T14:00:59Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'BB resolved: base propensity read certified. Phase 1 ran clean on Modal
    (3,447 s A10, ~$2; one aborted empty-HF-token launch caught inside a minute).
    Pre-launch: full red-team (1 invalidating finding, missing degenerate/schema_valid
    guard on the contrast cells in fit+score, fixed and regression-locked, smokes
    14/14; FID-2 gates.yaml repin 3f23b51f->33fe08ad adjudicated intent-preserving),
    two lead adjudications recorded pre-read (gradeable guard scope; G2 gradeable-only
    primary). Results: G0 205 confabs/1,020 refusals on guarded 1,662-row base fit
    surface; read-once gate on vendored 750: BB-P1-G1 PASS AUROC 0.8179, CI [0.7190,
    0.9042]; G2 caution 0.9820; FID-1/2 pass; near-dup 0 flagged. First certified
    propensity reading in the program, zero training. Resolved; PR #274 open; TODO
    BB updated (half c, base actuation, remains). Gotcha: modal CLI 1.5.1 volume get
    fails Errno 21 on directory trees; use Python SDK iterdir/read_file with skip-existing
    resume. KG-ingest queued post-merge.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'PR #273/#274 merges; ladder completion -> aggregates -> red-team; then H3/H4
    lane; BB half c amendment after snap hardened'
  signals: {}
- id: 026-checkpoint
  at: '2026-07-11T21:58:59Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Mistral probe-cell crash diagnosed and repaired pre-sweep: the in-pipeline
    gen-stream smoke probe was tied to max(dose_grid), so mistral''s sigma-mapped
    grid [6..27] made the probe inert (byte-identical output at strength 27, equal
    to the strongest arm) and the guard refused launch. This falsifies sigma-ladder
    transfer for mistral (inert at 29 sigma where llama responds at 5-13 sigma). Morning
    artifacts bracket mistral''s window empirically: inert at 27, fully degenerate
    at realized strength 106.5 (584/584 fired confabs at dose 100), tokens moving
    at 250. Fixes on exp/doubt-snap-cross-family commit b8e9c873: mistral grid revised
    pre-sweep/pre-outcome to log-span (27,100) = [30,38,46,56,67,80,92]; smoke probe
    decoupled to fixed 250.0; dated AMENDMENT extension + NOTEBOOK entry + pin refresh
    (no-further-grid-changes clause never triggered because the selection rule was
    never evaluated on [6..27]). Mistral relaunched detached batch-1 (app ap-WQXHAMrCooWjpskPgy36cH),
    weights loading, background poll armed. Skill PR #275 updated (cffaed77): rule
    4 now requires empirical per-cell bracketing (sigma-mapping is a first guess only);
    rule 6 gains the probe-decoupling gotcha. Llama sweep live and healthy: real interior
    dose-response, fired-confab clean_tighten 64->107->61 across strengths 5.3->9.1->12.4
    then collapse, peak ~18.5% well below the 0.60 selection floor, trending toward
    an honest FIT dose-viability null. Local 3090 midband ladder: baseline + hs20
    all arms + hs23 gated/permuted complete; hs23 random_direction on dose 6 of 7
    (~93%); hs26 and hs30 late-comparator cells remain (roughly a day-plus).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 027-checkpoint
  at: '2026-07-12T14:21:18Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'jspace-family-atlas full arc closed in one day: signed (2524891) with
    both predictions registered pre-launch (orchestrator and user both holds-on-both),
    launched with user approval (Modal ap-q2mU3RZwwrHyaTbr1ehwVm, $10 cap, ~$2 actual),
    resolved, PR #277 opened. Gates AG0/AG1/AG2 PASS with lead re-derivation from
    pulled captures. Prediction NOT MET both families (eff_dim_frac peaks early, 0.14/0.09
    depth, not interior); falsifier not triggered (non-monotone profile, readable
    interior band). Layer map delivered: llama ~L20-23 (raw refusal 0.90), mistral
    ~L15-17 (0.925). Red-team pre-verdict: fleet-audit 0.997-vs-0.90 reconciled as
    population definitions (refused-vs-known vs pooled-answered); random-direction
    control committed showing refused-vs-known norm confound (random up to 0.97) while
    caution/raw-refusal baselines stay 0.5-0.75. Exhaust-skill-builder assigned fleet
    HF dataset dry-run build (no upload; card for user approval). hs30 ladder comparator
    still running locally.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'Merge PR #277 on user OK; hold fleet resolve for hs30; review builder''s dry-run
    card; draft raw-refusal-axis actuation amendment using the atlas layer map'
  signals: {}
- id: 028-checkpoint
  at: '2026-07-12T15:00:25Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Atlas arc fully closed: PRs #277 (jspace-family-atlas resolved) and #278
    (family-atlas skill + docs/atlas/family-layer-map.md registry) MERGED with user
    approval; KG ingest committed and lead-verified (6f09ec14: experiment node + 2
    mechanisms - workspace-band-peak-location-is-family-relative, refused-vs-known-contrast-carries-norm-position-confound;
    validator 0 errors, manifest kg: list filled, exp validate OK). PI directive made
    standing: atlas extraction is the STANDARD for every new model/family/size before
    actuation design; axes assumed universal, layer band family/size relative, no
    cross-family layer porting. Doc janitor pass: TODO.md gained the dated 2026-07-12
    arc section (fleet/ladder/atlas/skill/raw-refusal candidate/HF backfill rows)
    + index regen; AGENTS.md (canonical) skills list completed to all nine and synced
    into CLAUDE.md (gotcha: CLAUDE.md orchestrator section is GENERATED from AGENTS.md,
    first edit got reverted by sync). Two finds lifted to PI: 7 untracked aux-head-era
    docs (pr118-120 reviews/prep) awaiting commit-or-archive call; untracked experiment/
    tree holds ~100GB local Phase 1 run products on canonical - no action without
    deliberate curation. In flight: exhaust-builder fleet HF dataset dry-run card;
    hs30 ladder arm.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - hs30 lands -> fleet resolve Outcome + ladder aggregates; review exhaust dry-run
    card with PI; draft raw-refusal-axis actuation amendment on the atlas layer map;
    PI call on aux-head doc strays
  signals: {}
- id: 029-checkpoint
  at: '2026-07-12T16:04:53Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Phase 1 outputs migration EXECUTED (commit 30fa503e): the untracked ~99GB
    experiment/ tree scouted (read-only inventory: 97.5GB unique research data, ZERO
    duplication vs 9.8MB code-only archive, bridge containment confirmed ABSENT locally,
    no tracked references), user approved the two decisions (shared bulk to gitignored
    archive/experiment/phase1-data/, 3.7MB junk deleted), migrator built a deterministic
    classifier (letter-to-slug from registry.json legacy.label, 40 mappings, flagged-not-guessed
    on amendment_a_*/mi_* dirs) with dry-run manifest which the lead reviewed and
    executed: 317/319 entries, 43.9GB to experiments/<slug>/analysis/phase1-migrated/
    (SR 26GB, Z 8.6GB, AH 6.7GB), 56GB shared to phase1-data, exp validate OK post-move.
    Two Amendment AI PAR eval dirs hold 14 Docker-era foreign-UID files: copied byte-verified
    to experiments/probe-as-reward, source residue (5.4MB) awaits operator sudo rm.
    Gotcha: shutil.move copy-fallback rmtree dies on foreign-owned entries; pre-move
    ownership scan (find ! -user) belongs in bulk-move scripts. Aux-head doc strays
    (7 files) still await PI commit-or-archive call.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - PI runs sudo rm -rf experiment residue; hs30 -> fleet resolve + raw-refusal draft;
    exhaust dry-run card review
  signals: {}
- id: 030-checkpoint
  at: '2026-07-13T02:53:31Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Ladder + fleet both RESOLVED same night. hs30 ladder completed 22:35 (74,753
    generations, ~59h wall, bs=8, clean exit). Lead recomputed headline aggregates
    from raw RunLogs pre-red-team (matched runner exactly); red-team over seven attack
    surfaces returned G1 SURVIVES, no invalidating finding; three lifted adjudications
    accepted (240-known cost denominator with 10/13 fired-known conditional reported
    alongside; in-sample FIT-only scope; official summary promoted to analysis-committed).
    qwen35-4b-midband-doubt-snap RESOLVED: G1 PASSES at hs20 dose 8x sigma_c, the
    unique cell in the locked 4x7 grid (refused 0.684, well-formed 0.980, known false-refusal
    0.042); falsifier does not fire; late comparator hs30 reproduces entangled failure
    in-grid; layer potency monotone toward earlier layers (hs20>hs23>hs26>hs30), echoing
    the atlas early-structure finding; PR #279. Red-team scope notes adopted verbatim:
    selectivity belongs to the c_hat write direction not the gate (permuted confabs
    refuse 0.669 vs gated 0.684; dosed knowns only 0.056); placebo magnitude-matched
    via readback; no optimum claim (hs20 is grid-edge, earlier layers untested). Fleet
    doubt-snap-cross-family-confirmatory then RESOLVED: NOT PROMOTED, prediction not
    met (uniform pre-outcome G0 dose-viability stops, peaks 0.326/0.184/0.000/0.058),
    falsifier wording gap recorded straight (binds held-out fails only); Outcome indicts
    the universal 0.94-depth write-site rule via c_hat audit + same-substrate ladder
    contrast (0.326 late vs 0.684 mid-band); both scoreboard predictors wrong on the
    fleet, both right on the ladder (orchestrator wrong on layer: hs20 not hs23);
    PR #280. Both PRs await user merge approval. KG ingest queued post-merge for both.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'User merge call on PRs #279/#280; KG-ingest both resolves post-merge; draft raw-refusal-axis
    actuation amendment (atlas layer map sites, exterior-shaped prediction/falsifier);
    review exhaust dry-run card; sudo rm residue + aux-head strays still pending PI'
  signals: {}
- id: 027-result
  at: '2026-07-13T11:16:48Z'
  kind: result
  title: 'H4 resolved all-gates-pass (PR #281); H3 signed; H6 launched then bounced
    on two harness bugs'
  summary: 'H4 red-team survived all five surfaces; Outcome written with two binding
    scope statements (60.1% is damage not refusal, decomposed 55.8pp false-refusal
    + 3.9pp wrong + 0.4pp degenerate, superseding the n=80 36.2% diagnostic; gate-supplies-selectivity
    bound to Qwen3-4B/L34/dose-200 and reconciled with the ladder permuted-gate result
    as operating-point dependence). Resolved, anchor checksums recorded, PR #281 open
    awaiting user merge approval. H3 signed after accepting all six builder adjudications
    (decisive: G3 placebo re-draws decode greedy, thresholds anchor to greedy precedent;
    Lane phrase sampled placebo arms adjudicated a drafting slip); six modules sha256-pinned
    by hand since exp sign pins configs only; evening 3090 slot. H6 launch-time resolution
    committed (revision 64033659, direction sha 9e0bf40c, 25-ID pool; scout report
    corrected twice: staging rows.jsonl has no question text, text lives in pools/ak_stage1_pool.jsonl;
    328 unique keys not 25) then both paths failed on harness plumbing: tuner device
    mismatch at evaluate_g2 (direction on cpu), bespoke pre-flight assert that may
    conflate readback misconstruction with the registered hook-does-not-fire prediction;
    unsloth also silently redirected the load to qwen3-4b-unsloth-bnb-4bit. Fix reassigned
    to h4-builder (h6-builder lane stalled behind the idle guard twice). RR raw-refusal
    design dispatched to fresh agent rr-drafter (heldout-drafter also guard-blocked):
    keeps doubt-gate arm per H4, atlas sites, Wilson gates, outcome-shape coverage,
    draft-only.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - H4 verdict adjudicated by lead; H3 placebo-decode ambiguity adjudicated greedy
    pre-launch; H6 pre-flight-vs-G1 conflation flagged as an adjudication the fixer
    must record, not silently fix
  next_steps:
  - 'h4-builder fixes+relaunches H6 (free 3090); lead launches H3 after H6 frees the
    card (GPU smoke first to calibrate throughput); rr-drafter delivers RR draft;
    H4 KG-ingest after PR #281 merges'
  signals: {}
- id: 028-result
  at: '2026-07-13T15:20:47Z'
  kind: result
  title: H3 G1 falsifier-fires pending red-team; H4/H6 merged+ingested; RR signed,
    staged, launch blocked on anchor-slice
  summary: 'H3 confirmatory run completed all four phases (443 greedy + 2215x3): G0
    PASS (greedy reproduces 73.5%/3.1% exactly), G2 PASS (sampled cost ~6% per-sample),
    G3 PASS (placebo re-draws robust all 5 seeds), G1 FAIL by collapse: pooled sampled
    majority-vote conversion 140/925=15.1% Wilson [13.0,17.6] vs 63.5% floor, all
    seeds fail individually, any-vote 53.2%, mean per-sample fraction 22.0%. If certified,
    the falsifier fires and the 73.5% headline re-scopes to one greedy decode (write
    dominates argmax, not the sampled distribution); BOTH scoreboard calls wrong.
    Verdict withheld pending ladder-red-team instrumentation pass on the batched sampled
    path (H6 lesson: silent hook non-delivery produces exactly this signature; surfaces:
    per-row readback in run_log_sampled, fired-vs-non-fired contrast, sampling config
    echo, batched termination/grading parity, independent majority-vote recompute).
    H4+H6 PRs #281/#282 MERGED on user approval; KG-ingest done (ac24f7db, 5 new nodes,
    operating-point reconciliation woven not contradicted). RR: signed with predictions
    (user: both families shape A; orchestrator: exactly one, lean mistral); harness
    built (c12e0578, 33 CPU tests) and lead-reviewed, all 7 builder adjudications
    accepted; lead repaired four sign-surviving cell.yaml placeholders via repin (revisions
    lead-verified vs fleet SSOT); stager landed row pools + full-depth atlas captures
    (coverage 1.0 both families, sha-verified); llama launch bounced on missing anchors_at_candidate_layers.json
    whose GPU-capture-deferred premise is false (staged tensors carry anchor__L0..L28
    full depth; pure CPU slice) - fix + relaunch with h4-builder.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - H3 falsifier verdict deliberately withheld until instrumentation is adversarially
    verified (adopt-no-null-from-uncertified-instrument, the AK/H6 rule); RR precondition-report
    naming quirk left as-is (cosmetic, pinned module)
  next_steps:
  - 'ladder-red-team H3 verdict -> adjudicate -> Outcome (falsifier straight if sound;
    artifact diagnosis if not) -> resolve -> PR; h4-builder anchor-slice fix -> llama
    then mistral RR cells; session tasks: HF backfill card still owed (task 24)'
  signals: {}
- id: 031-checkpoint
  at: '2026-07-13T23:06:42Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'RR + H3 both resolved in one arc. RR cross-family raw refusal: mistral
    leg completed shape F (peak hs16/dose12 refused 0.5793 vs 0.60 floor, Wilson straddles),
    red-teamed and CERTIFIED-NULL with a binding detector-width caveat (97 hand-verified
    mistral-idiom abstentions at the peak would clear the floor; llama''s F is robust
    to detector width, mistral''s is not); falsifier fired (neither family shape A),
    resolved falsified, PR #285 open awaiting PI merge approval; both scoreboard calls
    falsified. PI directive recorded: future abstention acceptance criteria include
    a registered blinded hand-check adjudication lane; RR2 successor drafted (exp/rr2-mistral-adjudicated-refusal,
    2f9da6d3): detector v2 screen + blinded symmetric adjudication lane as primary
    instrument, fixed operating point hs16/dose12, held-out leg only, sign blocked
    on #285 merge. H3: termination-rule artifact confirmed (764/769 term-only failures,
    eos-at-final-position, texts are clean refusals), harness fixed to is_terminated_naturally
    single source of truth (16/16 tests, parity exact 1056/1480 and 130/185), repinned
    d722811e, pre-fix logs archived; full K=5 re-run on fixed harness passes ALL gates
    (G1 pooled 69.5 pct vs 63.5 floor, every seed above; G2/G3/G0 identical to pre-fix
    run; seed-20260710 exactly 130/185 = triple agreement), verdict REVISED to resolved
    (headline survives sampling), both scoreboard calls correct on corrected instrument,
    PR #283 back to ready with revised resolve (bba2cee5). Next: PI merges #285 and
    #283; RR2 sign (needs PI scoreboard prediction); held-out ladder sign + GPU sequence;
    skill rule for blinded adjudication lane after RR2 design approval; KG-ingest
    both verdicts post-merge.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 030-result
  at: '2026-07-14T02:49:12Z'
  kind: result
  title: Held-out ladder promotes shape A; RR2 resolves falsified on certified placebo
    fire
  summary: 'qwen35-4b-midband-heldout resolved shape A and merged (PR #287): frozen
    hs20 point transfers to fresh held-out rows, fired-confab refused 872/1286 = 0.678
    (Wilson [0.652, 0.703]) vs 0.60 floor, wf 0.977, gated-arm known cost 14/360 =
    0.039, random no-op, permuted strictly worse; both scoreboard calls correct. Abstention-grading
    standard institutionalized (PR #286): frozen detector screen + registered blinded
    adjudication lane, manifest-before-grading and hash-before-unblinding in code,
    falsifier closes the regress. RR2 (rr2-mistral-adjudicated-refusal-confirm) then
    ran the full blinded protocol as its reference implementation: context-free agent
    graded 3582 texts blind (626 TRUE), hash committed pre-unblinding. RG1 PASS 911/1303
    = 0.699 [0.674, 0.723] wf 0.987 (both pre-registered bands hit; RR detector-width
    caveat vindicated, the idiom-inclusive refusal is real with pristine cost 2/382).
    RG2 PASS. RG3 FAIL: baseline confab adjudicated abstention 0.280 vs random_direction
    0.354, +7.39 points vs the 2-point tolerance; the wide instrument reveals 28%
    undosed baseline abstention the narrow detector read as ~0. Red-team certified
    the fire across five surfaces (decisive: 435-decoy audit, 255/255 clear-negative
    agreement, conservative on positives; 160-row baseline re-read 2/160 disagreements
    both widening the delta; random-arm excess is genuine well-formed hedge content).
    Resolved falsified as registered, no rescoring lane; both shape-A scoreboard calls
    incorrect on the verdict while nearly exact on the benefit level. PR #288 open,
    merge held for user approval.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - 'Falsifier fire CERTIFIED, verdict falsified as registered; gated lift +41.9 points
    (5.7x random) noted as interpretation only, RG3 is a tolerance test not a ratio
    test, goalposts stand. Forward rule recorded in the Outcome: any successor registers
    its placebo tolerance (or a pre-stated effect-ratio gate) against the wide-instrument
    baseline before new data, as a new signed amendment.'
  next_steps:
  - 'User merge decision on PR #288; KG-ingest RR2 verdict post-merge; possible successor
    design note needs user sign-off; HF exhaust backfill (#24) now includes H3/RR/heldout/RR2
    candidates.'
  signals: {}
- id: 031-result
  at: '2026-07-14T12:38:29Z'
  kind: result
  title: 'Calibration study resolved: family-graded wide baselines; qwen placebo suppresses'
  summary: 'abstention-wide-instrument-calibration ran end-to-end in one day, CPU-only:
    signed with detector v2 byte-identical to RR2 pins, 31,620 rows staged, 11,788-core
    blinded pool across 17 cell-scoped shards, seven context-free graders, manifest-before-grading
    and hash-before-unblinding held throughout. Mid-run instrument correction (H3-pattern,
    repinned, red-team-verified): attempt-1 opaque ids collided across (hs_index,
    dose) in the QL ladder cell; blinding and per-line grades unaffected; join corrected
    to positional. QL cell voided terminally per registered CG1 second-failure rule
    (two independent graders failed the same 14-decoy clear-positive draw at 0.286/0.429;
    ten other QL shards passed 0.692-0.929); reported straight as narrow-only. Red-team
    CERTIFIED-MEASUREMENTS with bit-for-bit recompute. Certified table: qwen wide
    baseline 0.104 [0.089,0.122], llama 0.164 [0.146,0.184] (lower bound due to unknown_refused
    carve), mistral 0.280 cited; undercounts 6.1/12.9/12.2 points. Headline surprise:
    qwen paired placebo delta is NEGATIVE, -5.13 points wide (0.108 to 0.057, non-overlapping
    CIs) where mistral recruits +7.39: placebo response is family-specific in SIGN.
    Falsifier adjudicated not fired on the signed consequent-coherent reading (an
    absolute reading would assert program-wide perturbation-recruited hedging that
    the suppression contradicts); red-team independently recommended the same. Prediction
    not cleanly confirmed: placebo near-no-op leg missed in magnitude, llama band
    missed at 0.164; scoreboard: user correct on per-family differences and qwen baseline,
    incorrect on placebo magnitude; orchestrator additionally incorrect on llama.
    Resolved; PR #289 open, merge held for user.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - 'Falsifier reading adjudicated signed/consequent-coherent under red-team certification,
    not chosen for the scoreboard; QL void reported straight, no third grading attempt;
    successor design rule recorded: no flat small symmetric placebo tolerance, register
    against per-family wide baselines with two-sided tolerance or effect-ratio gate;
    CG1 lesson: pooled or larger clear-positive decoy draws per shard.'
  next_steps:
  - 'User merge decision on PR #289; KG-ingest calibration verdict post-merge; abstention-grading
    skill update (CG1 granularity + decoy-carve coverage lesson) as separate PR; RR2
    successor design can now register its placebo criterion against the measured baselines
    (needs user sign-off); HF exhaust backlog #24 grows by this experiment.'
  signals: {}
- id: 032-decision
  at: '2026-07-14T13:22:02Z'
  kind: decision
  title: RR3 pre-run scoreboard calls + Q3 framing (PI + orchestrator)
  summary: 'RR3 (rr3-corrected-placebo-replication, draft on exp/rr3-corrected-placebo)
    pre-run registrations, stated BEFORE harness build and any run. Q3 framing decided
    by PI: mistral core verdict is reported as a corrected-criterion re-adjudication
    of RR2''s claim (same test done more intelligently, with the rider as additional
    data exhaust), not as a fresh confirmatory replication. Scoreboard calls. PI:
    llama placebo sign NULL (model is old and an outlier in his read); mistral RG1
    PASS; mistral fresh random seeds INSIDE the +/-8 descriptive envelope. Orchestrator:
    llama placebo sign WEAK RECRUITMENT (positive, monotone-in-baseline reading of
    the calibration sign map: llama wide baseline 0.164 sits between qwen 0.104 suppression
    and mistral 0.280 recruitment); mistral RG1 PASS; at least one of the K fresh
    mistral random seeds lands OUTSIDE the +/-8 envelope on the recruitment side while
    staying below the ~14-pt gate-fail threshold. These get copied verbatim into the
    AMENDMENT scoreboard at sign-off; no edits after results per the no-goalpost rule.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - 'Q3: corrected-criterion re-adjudication framing (PI). Scoreboard calls registered
    as above.'
  next_steps:
  - rr3-reviser lands revision -> lead final review -> copy scoreboard calls into
    AMENDMENT -> harness build -> sign with pins -> lift GPU launch approval to PI.
  signals: {}
- id: 033-launch
  at: '2026-07-14T17:05:58Z'
  kind: launch
  title: RR3 signed and launched on local 3090
  summary: 'RR3 (rr3-corrected-placebo-replication) arc completed draft-to-launch
    in one day. Draft (opus agent) -> lead revision round (Q1 regeneration kept, Q2
    max-over-K, Q4 full grid, Q5 scoreboard slots, +/-8 descriptive envelope, >=25
    clear-positive draws, rider dosing of answerable rows with source-field question-type
    stratification) -> PI resolved Q3 (corrected-criterion re-adjudication framing)
    and gave scoreboard calls (llama null / RG1 pass / seeds inside; orchestrator
    counter: llama weak recruitment / RG1 pass / one seed outside) -> harness build
    (15 modules, 78-test suite, detector v2 byte-identical to RR2/calibration pins,
    held-back decoy pool, pooled CG1 floor, max-over-K arithmetic proven by test)
    -> lead fixed the build''s STOP item (cell.yaml rider_cells YAML parse error introduced
    in the revision commit; shared config hoisted to rider_shared), pinned llama revision
    006f5dcd (verified RR cell.yaml + fleet model_matrix agree), confirmed K-seeds
    [30260714, 30260715, 30260716], SIGNED. Paper 5 manuscript updated on main with
    RR2 falsification + calibration Section 4.8 (cfdc90d7). Calibration KG-ingest
    committed (06f525b2). LAUNCH: local 3090 (free lane, standing approval, PI also
    explicitly approved after the auto-mode classifier flagged the --i-know-this-runs-on-gpu
    acknowledgment flag; PI said proceed). First launch attempt stopped cleanly pre-GPU:
    staged inputs absent in fresh worktree; fixed by symlinking RR worktree row pools
    + atlas captures (gitignored row-level artifacts, correct lane). Relaunch passed
    materialize for both families (mistral 1312/382, llama 2956 joined) and entered
    fit_reuse RG0.'
  evidence: []
  run_ids:
  - rr3-pipeline-20260714b
  commands:
  - pipeline.py all --batch-size 8 --i-know-this-runs-on-gpu (local 3090, detached,
    log analysis/pipeline_run_20260714b.log)
  decisions: []
  next_steps:
  - 'On pipeline completion: RG0 byte-repro verify, build adjudication pool, commit
    pool manifest, dispatch context-free blind graders, hash-commit, CG1, scorer,
    red-team certification BEFORE verdict. Pending elsewhere: sign-flip analysis amendment
    draft (#39), abstention-grading skill PR (#42), scale test 1.7B+~9B held for RR3
    (#41).'
  signals: {}
- id: 034-decision
  at: '2026-07-14T17:50:03Z'
  kind: decision
  title: 'Sign-flip analysis: pre-run scoreboard calls + structural finding'
  summary: 'placebo-signflip-question-type-analysis (draft on exp/placebo-signflip-analysis)
    pre-run registrations. Drafter''s structural finding, lead-verified bit-for-bit
    from row_level_scored.jsonl: every dosed placebo row in every family/cell is unanswerable
    (kuq), so the certified cross-family sign difference (qwen -5.13 suppression vs
    mistral +7.39 recruitment) was measured entirely on the unanswerable stratum and
    question type CANNOT explain it behaviorally on existing data (it never varied).
    Powered question-type tests move to the mechanism leg (anchors exist for both
    types in all three families) and prospectively to RR3''s rider. Scoreboard calls
    (PI then orchestrator): M1 answerable-vs-unanswerable separation on doubt/caution
    axis in all three families: YES / YES. kuq-subtype concentration of the placebo
    effect: CONCENTRATED-OR-UNEVEN / EVEN-SPREAD (differentiating slot). M3 realized
    displacement differs by type: YES / YES. Lead decisions: subtype breakdown extended
    to mistral; mistral hs16 directions provenance-by-regeneration via RR fit manifest.
    RR3 pipeline meanwhile mid-generation on the 3090 (92 percent util).'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - Scoreboard registered as above; subtype breakdown extended to mistral; directions
    provenance-by-regeneration.
  next_steps:
  - 'Harness build for signflip analysis (BG1 exact frame-port acceptance test is
    the known risk) -> lead review -> sign -> CPU run -> red-team -> resolve. RR3:
    await pipeline completion notification.'
  signals: {}
- id: 035-checkpoint
  at: '2026-07-14T18:27:53Z'
  kind: checkpoint
  title: 'Pre-restart state: RR3 generating, sign-flip behavioral leg done'
  summary: 'PI will restart the machine once the RR3 GPU run completes; session pauses
    there. STATE AT PAUSE. RR3 (exp/rr3-corrected-placebo, signed): pipeline through
    mistral core (all 4 arms + 3 seeds) and heldback passes; mistral rider in progress,
    llama rider remains; log analysis/pipeline_run_20260714b.log; on completion DO
    NOT dispatch adjudication until resume. Sign-flip (exp/placebo-signflip-analysis,
    SIGNED, run partially executed): BG0/BG1/BG2 all PASS (BG1 frame port 1303/1303
    exact firings, 0/1692 mismatches; BG0 reproduced both certified deltas bit-for-bit).
    Behavioral leg executed: qwen suppression CONCENTRATED in future-unknown subtype
    (-24.7 pts, n=190, baseline 0.332) vs -2.8 or less elsewhere; mistral recruitment
    broad-based positive (+3.8 to +11.8 across all six subtypes); baseline hedging
    orders subtypes identically across families. PI scoreboard call (concentrated-or-uneven)
    currently winning vs orchestrator (even-spread); near the registered inert-reading
    falsifier for qwen; NO verdict yet, red-team required first, mechanism leg (M1/M2/M3)
    NOT run (deferred for host RAM until GPU job ends). Report at analysis-committed/signflip_report.json,
    uncommitted. RESUME SEQUENCE: 1) verify RR3 pipeline completed cleanly (RG0 byte-repro
    in log), 2) run sign-flip mechanism leg (opt-in real-data loaders incl. mistral
    251MB / llama 493MB anchor JSONs), 3) rerun report.py, commit report, 4) red-team
    certification of sign-flip, resolve, PR; 5) RR3 adjudication cycle: build_adjudication_pool,
    commit pool manifest BEFORE grading, context-free blind graders, hash-commit before
    unblinding, CG1, rr3_scorer, red-team, resolve, PR. Scoreboards registered in
    both AMENDMENTs; no goalpost moves.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Await RR3 pipeline completion notification; then checkpoint again and tell the
    PI it is safe to restart.
  signals: {}
- id: 036-checkpoint
  at: '2026-07-14T19:13:13Z'
  kind: checkpoint
  title: RR3 generation COMPLETE; machine quiesced for PI restart
  summary: 'RR3 pipeline exited 0 after the full sequence (materialize both families,
    fit_reuse RG0 reconstruction, heldback passes, mistral core all arms, mistral
    rider, llama rider). GPU freed (0 MiB). Runlog artifacts on disk in the rr3-corrected-placebo
    worktree analysis/runlog/: core baseline 1694 rows, gated 1303 fired (matches
    RR2''s fired count exactly), three random seeds (30260714/15/16), dose_knowns
    382, heldback passes, 87 rider files (mistral + llama dose ladders incl. answerable-row
    legs). Pipeline printed the 5-step adjudication instructions and stopped, as designed;
    nothing dispatched. Sign-flip behavioral leg done earlier (gates pass, PI subtype
    call ahead), mechanism leg deferred. NOTHING RUNNING: no background tasks, no
    agents in flight, both amendment branches committed locally, main pushed. Safe
    to restart the machine. RESUME: follow the pre-restart checkpoint''s resume sequence
    (verify RG0 byte-repro explicitly as step 1: the log does not print an explicit
    byte-repro line; confirm whether the check ran in-pipeline or runs in the scorer
    before adjudication dispatch).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'After PI restart: RG0 byte-repro verification, then sign-flip mechanism leg (RAM
    now free), then RR3 adjudication cycle per the printed instructions.'
  signals: {}
- id: 037-checkpoint
  at: '2026-07-14T20:18:57Z'
  kind: checkpoint
  title: Checkpoint
  summary: RR3 adjudication cycle DISPATCHED. Pool manifest (21 shards, 16045 rows
    = 14485 core + 474 clear-neg + 1086 clear-pos decoys, seed 20260715) committed
    to exp/rr3-corrected-placebo as 6204a7f2 BEFORE any grading, per the manifest-before-grading
    rule. 21 context-free blind graders (sonnet, rubric verbatim from AMENDMENT.md,
    bare opaque_id+text shards, no experiment context, no pattern-matcher per standing
    PI directive) spawned in parallel; graded files land in gitignored analysis/graded/.
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'On grader completion: verify line counts/order, apply_adjudication.py commit-hash
    per shard BEFORE apply, then apply --grading-manifest (CG1 per-shard + pooled,
    void-regrade-once), then rr3_scorer.py, then red-team BEFORE verdict. signflip-mech
    agent still running (BG1 mistral/llama real-data checks + M1/M2/M3 mechanism leg).'
  signals: {}
- id: 038-checkpoint
  at: '2026-07-14T20:38:58Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'INCIDENT + containment during RR3 blind grading: parallel grader agents
    shared the session scratchpad for helper scripts and two write collisions occurred
    on generic filenames (write_shard00.py, verify.py two writers each). Effect: one
    grader''s judgment chunk routed to the wrong target mid-run; the in-flight rider_mistral_shard_01
    grader''s partial file is missing a ~50-line middle block (720/770, own ids only,
    no foreign ids). Damage CONTAINED: all 20 completed shards pass full independent
    integrity (exact counts, positional opaque_id match, no dups within/across files)
    and every hash commitment was recorded only after that verification; the damaged
    shard was never hash-committed. PI directive adopted as standing rule: any parallelized
    agents get pre-assigned PRIVATE working dirs for all intermediates plus unique
    output paths, forbidden to write elsewhere; zero shared mutable paths. Fold into
    abstention-grading skill update. Separately: BG1 diagnosis confirmed mistral check-scope
    defect (0/1694 mismatches on the true evaluated roster; check iterates full 3037-row
    anchor population, frame_port.py:199-238); llama recompute still running.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Await rm01 grader; if final file not cleanly repaired, void attempt (never committed,
    no unblinding) and dispatch fresh grader with private dir. Then git-commit grading
    manifest, apply (CG1), rr3_scorer, red-team. Await llama half of BG1 diagnosis,
    then adjudicate instrument-defect repin vs genuine fail.
  signals: {}
- id: 039-checkpoint
  at: '2026-07-14T20:56:06Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'RR3 RESOLVED FALSIFIED, PR #290 open awaiting PI merge approval. Full
    adjudication cycle completed: 21/21 shards graded blind and hash-committed pre-unblind
    (7cec7511), CG1 all-pass per-shard + pooled 0.782, apply clean (14485 rows), scorer:
    RG1 FAIL effect ratio 1.87 < 3.0 (gated lift +40.9 pts vs fresh random-seed lifts
    +13.3/-7.4/+21.8 at matched magnitude), RG2/RG3 PASS reproducing RR2. Opus red-team
    certified artifact-free across all six attack surfaces (directions genuinely random
    |cos|<=0.015, magnitude-matched, robust detector-only 1.91 and mean-denominator
    2.89). Outcome written, resolved falsified, registry regenerated (abaaaf99). Scoreboard
    adjudicated: PI right llama-null (rider null through 16x, +0.1 at 12x); both wrong
    on mistral RG1 PASS calls; envelope split (PI inside wrong, orchestrator outside
    right but 21.8 exceeded his 14-pt bound). KEY METHODOLOGICAL FACT for sign-flip
    and paper 5: single-seed placebo readings on mistral span -7.4 to +21.8 pts at
    12 sigma_c; calibration family-signed placebo map points are single draws; signflip
    adjudication must read RR3 Outcome first (cross-experiment note in Outcome).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - '1) PI decision: merge PR #290. 2) signflip: await llama half of bg1-diagnosis
    (mistral half confirmed check-scope defect, 0/1694 restricted mismatches), then
    adjudicate repin-vs-drop, then mechanism leg, with RR3 seed-variance caveat folded
    into any verdict. 3) Paper 5 update for RR3 result after merge. 4) Abstention-grading
    skill update #42 (+ private-workdir rule).'
  signals: {}
- id: 040-checkpoint
  at: '2026-07-14T22:09:57Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Signflip BG1 adjudicated and closed: both real-data fire-set failures
    were CHECK-SCOPE defects (lead re-derived mistral 0/1694 restricted personally;
    llama restricted 1/581 hs20, 0/581 hs22/hs23, known-presence invariant true, read
    from the diagnostic''s raw output log after the diagnostic agent stalled on an
    unwoken background job). frame_port.py corrected to the actually-gate-evaluated
    populations (no frame-math change), llama fire-set now gates at 1% tolerance (strictness
    increase), repinned with full reason, smoke 31 pass, corrected BG1 rerun ALL GREEN
    (41ae0e37 on exp/placebo-signflip-analysis, after one stale-registry-hook recommit).
    Mechanism leg (M1/M2/M3 + pre-stated subtype readout) dispatched to harness-builder
    signflip-mech2. Also this segment: paper 5 updated on main 4bb46ba6 (new 4.9 +
    seed-variance rule + Section 5 table correction + RR3 AMENDMENT stale-header fix);
    abstention-grading skill PR #291 MERGED (8bbaa8a1); data-exhaust copy-everything
    builder + completeness verifier PR #292 OPEN (validated: 4 experiments had zero-file
    verify-PASSing builds under old allowlist; all 22 slugs rebuild complete, v2 staging
    in scratch/exhaust-backfill-v2); doubt-snap dry-run card ready, publish awaiting
    PI go (use v2 build).'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - '1) Review signflip-mech2 M1/M2/M3 + subtype readout, then red-team, then falsifier/scoreboard
    adjudication + Outcome + resolve + PR (carry RR3 seed-variance caveat). 2) PI:
    merge PR #292; publish approvals per dataset card (doubt-snap first, from v2).
    3) Scaffold placebo seed-distribution census amendment (PI approved as next experiment)
    after signflip resolves. 4) Then scale test #41.'
  signals: {}
- id: 041-checkpoint
  at: '2026-07-14T22:40:03Z'
  kind: checkpoint
  title: Checkpoint
  summary: 'Signflip experiment RESOLVED (PR #293 open, awaiting user merge). Red-team
    certified all mechanism numbers to full float precision (fire-set 1303/1303; circularity
    discharged via held-out restriction, -6.05 vs -5.80). M1 axis question resolved
    from locked instruments: frozen gate defines doubt = -z_d, so doubt axis CONFIRMED
    all three families under operational convention (near-tautology caveat stated);
    caution axis not interpretable as question-type ordering; raw-axis prediction_consistent
    booleans NOT transcribed. Registered falsifier UNTRIGGERED (sign-agnostic, no
    CI spans 0); behavioral subtype arm FIRES for qwen (future-unknown -24.7 vs <=-2.8;
    also mistral''s +11.8 max and both families'' projection outlier). Scoreboard:
    M1 both correct; subtype PI correct / orchestrator WRONG; M3 both wrong for qwen
    (null), mistral non-null but 0.3% negligible. M2 carried RR3 single-seed caveat.
    Stale scaffold header corrected (same bug as RR3). Commit 7904da93, registry regenned,
    validate OK 72.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - 'User decisions pending: merge PR #293 (signflip), merge PR #292 (data-exhaust),
    doubt-snap publish go (v2 build). Then scaffold placebo seed-distribution census
    (K=10-20 seeds/family at matched magnitude, approved), then scale test.'
  signals: {}
---
# Paper 5 J-space hardening

## Question

Which registered follow-up experiments harden the Paper 5 actuation thesis, starting with a fresh Qwen3-4B J-space layer-site replication?

## Trajectory Position

Paper 5 has a v0 synthesis draft on main. The immediate hardening target is the
resolved J-space calibrated layer contrast: before treating the hs23/hs29
mid-band advantage as robust, rerun the same frozen directions/gates/doses on a
fresh raw-base Qwen3-4B private evaluation pool disjoint from the predecessor
fit and held-out rows.

## Summary

Session opened to turn the Paper 5 hardening plan into registered experiments.
First target is `experiments/j-space-layer-contrast-replication-qwen3-4b/`.
Row audit found enough candidate supply in the AH expansion pool: 13,496
expansion candidates, including 3,496 unknown and 10,000 known rows, with
12,923 row keys outside the prior J-space split. Existing expansion scores are
probe metadata, not behavioral confab/correct labels, so the replication needs a
fresh private raw-base generation pass to mine confab and known-correct eval
rows before the layer contrast.

## Checkpoints

### 001-planning - Paper 5 hardening route

- time: 2026-07-08T16:59:27Z
- kind: planning
- evidence:
  - `papers/paper-5-actuation/manuscript.md`
  - `experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md`
- summary: >
    Chose the narrowest hardening experiment first: same-model fresh-pool
    replication of the J-space layer-site contrast. Cross-family J-space sweeps
    remain queued after this result holds or breaks. Dense/multilingual token
    packing stays separate from layer-site replication so it does not move the
    token-target falsification goalposts.

### 002-observation - Fresh row supply audit

- time: 2026-07-08T16:59:27Z
- kind: observation
- evidence:
  - `/home/profsynapse/code/Epistemic-Humility-Research/archive/experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl`
  - `experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`
- summary: >
    Prior J-space split used 739 row keys: 309 confab and 430
    known_correct_answered, with 443 held out. The AH expansion pool has 13,496
    candidate rows, including 3,496 unknown and 10,000 known rows, and 12,923
    keys are fresh relative to the prior split. The expansion score file does
    not carry behavioral confab/correct labels, so fresh labels must be mined by
    raw-base generation before the replication contrast launches.

### 003-amendment - Fresh-pool replication scaffold

- time: 2026-07-08T16:59:27Z
- kind: amendment
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/cell.yaml`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/gates.yaml`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/extract_fresh_anchor.py`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/run_contrast.py`
- summary: >
    Scaffolded a Tier-2 exploratory replication using predecessor directions,
    gates, and calibrated doses frozen. New pool-mining script excludes all
    predecessor split keys and targets at least 200 fresh confabs plus 300 fresh
    known-correct rows. Fresh text, aliases, generations, and activations stay
    gitignored under analysis/; committed outputs are limited to ID-only pool
    manifest and aggregate summary.

### 004-observation - Fresh unknown confab density preflight

- time: 2026-07-08T17:08:00Z
- kind: observation
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_pool_generations.jsonl`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_eval_rows.jsonl`
- summary: >
    The full pool-mining preflight was stopped after 250 fresh unknown rows to
    estimate supply before spending the full run. It found 17 fresh confabs
    (6.8%), lower than the tiny smoke. At that density, the available AH
    expansion unknown supply should support roughly 200 fresh confabs but 250 is
    too tight. Before signing and before any layer-contrast outcome, G0 target
    was adjusted from >=250 confabs to >=200 confabs while keeping
    known_correct_answered at >=300. This remains at least as powered as the
    predecessor's 185-confab held-out contrast.

### 005-instrumentation - Exhaustive fresh-pool census mode

- time: 2026-07-08T17:30:00Z
- kind: instrumentation
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md`
  - `docs/datasets/jspace-fresh-pool-public-census-plan.md`
  - `datasets/kuq/dataset.md`
  - `datasets/popqa/dataset.md`
  - `datasets/triviaqa-rc-nocontext/dataset.md`
  - `datasets/selfaware/dataset.md`
- summary: >
    Added a resumable `--scan-all-candidates` mode to the fresh-pool miner so
    the same AH expansion candidate universe can be exhaustively censused for
    future reuse while the current replication remains governed by minimum G0
    floors. Public release is explicitly split from the experiment: committed
    artifacts remain ID/provenance/role metadata only, while question text,
    aliases, and model generations stay private under `analysis/` until
    per-source redistribution terms are audited. Local dataset cards currently
    mark KUQ as MIT and SelfAware as Apache-2.0; PopQA and TriviaQA need
    stricter publication review before raw-text release.

### 006-publication - HF dataset release boundary

- time: 2026-07-08T17:53:28Z
- kind: publication
- evidence:
  - `.skills/experiment-runner/reference/hf-publication.md`
  - `docs/datasets/jspace-fresh-pool-public-census-plan.md`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py`
- summary: >
    User requested publishing the completed census to the project Hugging Face
    account and keeping PR/merge checkpoints current for easy handoff. The safe
    release boundary is an ID/provenance/behavior-flag dataset plus rebuild
    instructions, not raw question text, aliases, prompt text, or generation
    text. After exhaustive scan completion, rebuild the text-free manifest,
    upload that public-safe dataset artifact, record the HF repo and revision in
    docs, then PR and merge the publication record before launching the signed
    layer-contrast experiment.

### 007-handoff - Census run checkpoint

- time: 2026-07-08T17:58:00Z
- kind: handoff
- evidence:
  - `HANDOFF-jspace-layer-replication-qwen3-4b.md`
  - `/home/profsynapse/code/ehr-worktrees/jspace-layer-replication/experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_pool_generations.jsonl`
  - `/home/profsynapse/code/ehr-worktrees/jspace-layer-replication/experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_eval_rows.jsonl`
- summary: >
    PR #256 merged the scaffold to main as 253dfc27. Exhaustive fresh-pool
    census continues locally in the jspace-layer-replication worktree. Latest
    persisted checkpoint: 3,730 generated rows, 306 selected confabs, and 37
    selected known_correct_answered rows. The confab side of G0 is cleared; the
    known-correct side is still running toward 300. Root handoff note records
    exact process, paths, resume commands, and next steps for HF upload,
    publication-record PR/merge, signing, anchor extraction, smoke, and full
    layer contrast.

### 008-publication - HF exporter prepared

- time: 2026-07-08T18:19:00Z
- kind: publication
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/build_hf_public_census.py`
  - `docs/datasets/jspace-fresh-pool-public-census-plan.md`
  - `docs/public-artifacts.md`
- summary: >
    Added a deterministic exporter for the planned public-safe HF dataset:
    `build_hf_public_census.py` reads the text-free manifest generated after
    `mine_fresh_eval_pool.py --manifest-only` and writes an HF-ready directory
    with `README.md`, `manifest.json`, `generated_rows.jsonl`, and
    `selected_rows.jsonl`. `docs/public-artifacts.md` now lists the planned repo
    `professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b` with the same
    no-text/no-alias/no-generation boundary.

### 009-publication - Exhaustive census published

- time: 2026-07-08T20:07:00Z
- kind: publication
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis-committed/fresh_eval_pool_manifest.json`
  - `docs/public-artifacts.md`
  - `https://huggingface.co/datasets/professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b`
- summary: >
    Exhaustive fresh-pool census completed: 12,923 generated candidates
    (3,305 unknown, 9,618 known), selecting 306 fresh confabs and 1,957
    known_correct_answered rows. Public-safe HF dataset uploaded to
    `professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b` at revision
    `3add102ce930f73a29013f572f03e7325da30825`. Upload contains only
    ID/provenance/role/behavior flags and excludes question text, aliases,
    prompt text, generation text, hidden states, and intervention outputs.

### 010-prep - Anchor extraction and smoke pass

- time: 2026-07-08T20:46:47Z
- kind: prep
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_anchor_extract_manifest.json`
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/smoke_summary.json`
- summary: >
    Local 3090 prep completed over the full selected fresh pool. Anchor
    extraction covered all 2,263 selected rows at hs23/26/29/34 in 83.2s. Smoke
    contrast passed G0: `g0_smoke_pass=true`, readback means were hs23=24.9998,
    hs26=74.9788, hs29=125.0104, hs34=174.9906, every layer had
    `frac_readback_within_tol=1.0`, and dosed-row collapse was 0.0 for every
    layer. Full outcome run remains held until the user prediction is recorded
    and the amendment is signed.
### 011-decision - Decision

- at: `2026-07-09T13:54:25Z`
- kind: `decision`
- summary: Replication signed and launched; cross-family queued with dedup constraint. User prediction recorded (full replication, +18-25pp) alongside orchestrator (holds-but-shrinks, +10-18pp); j-space-layer-contrast-replication signed (826d9a1c on agent/jspace-full-run) and the full 4-layer contrast launched on the local 3090. Scaffolded j-space-cross-family-layer-contrast (d2134050 on exp/j-space-cross-family-layer-contrast) using Amendment Z's family panel. Worktree audit found the signed doubt-snap-cross-family-confirmatory mid-run on Modal over an overlapping panel: to avoid duplicating its per-family FIT pipeline, the cross-family layer contrast HOLDS unsigned until that run resolves and is revised to consume its pools/splits/late-site artifacts. Also inherited its pre-outcome loader finding by substituting Mistral-7B-Instruct-v0.3 for Amendment Z's Ministral-3-3B (Mistral3ForConditionalGeneration is not a causal-LM write substrate). Open decision points for sign time: G3 late-reference floor 0.40/0.30 is a draft guess; multimodal loader paths and per-family EOS lists unverified.
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md`
  - `/home/profsynapse/code/ehr-worktrees/jspace-cross-family/experiments/j-space-cross-family-layer-contrast/AMENDMENT.md`
  - `/home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md`
### 012-result - Result

- at: `2026-07-09T17:28:55Z`
- kind: `result`
- summary: Replication resolved: registered G1 FAIL (null-result), PR #263. Full run completed flawlessly on the 3090 (exact readback, zero collapse, all 2,263 rows x 4 arms). Best mid-band hs29 99.67% vs hs34 94.12% = +5.6pp, under the 10pp bar; G2/G3 passed; both scoreboard predictions wrong. Post-run red-team reproduced every number and corrected the mechanism story before the Outcome was written: ceiling effect with a structural cause (fresh confabs single-source kuq_ku_unknown_x, the two harder predecessor sources absent from the candidate universe), so this is a narrower-distribution replication; direction survives with CI separation at hs23/hs29 (not hs26); hs34 deficit is write-effectiveness not gate-transfer; hs29 has the worst known-correct cost. Carried forward: Paper 5 pool-sensitivity caveat; cross-family experiment needs a ceiling-robust G1 (CI separation + failure-ratio) and multi-source confab mining before sign. Infra shipped same session: tuner RunLog (Synaptic-Tuner PR #141) + consumption/skill invariant (PR #262) after catching the buffered-run risk mid-flight; per-row persistence gap in this run is the motivating case.
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md`
  - `https://github.com/ProfSynapse/Epistemic-Humility-Research/pull/263`
### 013-interpretation - Interpretation

- at: `2026-07-09T19:21:21Z`
- kind: `interpretation`
- summary: Qwen3.5 doubt-snap dose-fit failure audited: overdose collapse, NOT a family null and NOT an inert write. Opus audit of the Modal artifacts falsified the hook-path/inert-write hypothesis (readback write_ok=true, commanded ~100 realized 99.96-100.04, layer 29 correctly derived from nested text_config) and the grader/render hypothesis (baseline well-formed 0.995/0.987). Root cause for BOTH cells: the registered absolute dose grid {100,150,200,250} is mis-scaled to Qwen3.5 residual geometry. Qwen3.5-4B sigma_c=2.80 (4.7x smaller than the working Qwen3-4B reference) puts even dose 100 at 38-sigma: 854/854 fired confabs degenerate (repeating I-dont-know token to cap). Qwen3.5-9B shows textbook dose-graded collapse: refused 18->363->886 across 100->150->200 while well_formed falls 886->503->2 (JSON colon corrupts before content); peak clean 5.1% at dose 150; its coherent window sits below/between the grid. Key science: sigma-distance is NOT portable across models (9B at 15.8 sigma matched the reference's working point and still collapsed); usable windows are absolute and model-specific, consistent with the J-space dose-calibration prior. Disposition: instrument failure, NOT-RUN candidates, must not be reported as doubt-snap-null-on-Qwen3.5 (9B refuses 97% of confabs on command). Honest limit: no proof a window clearing 60%/10% exists; grid never sampled below 100. Gap found: Modal rows carry no per-row readback field (smoke-only), unlike the local pipeline. Proposed (NOT run): finer low grids (4B ~10-75, 9B ~60-140) reusing volume artifacts, ~1-2 GPU-h ~$1-3/cell, but this changes the LOCKED grid and needs a signed revision -- lifted to user.
- evidence:
  - `/home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/analysis/from_modal/qwen35_4b/committed/dose_fit.json`
  - `/home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/analysis/from_modal/qwen35_9b/committed/build_manifest.json`
### 014-amendment - Qwen3.5 dose-grid recalibration registered + relaunch dispatched

- at: `2026-07-09T20:59:59Z`
- kind: `amendment`
- summary: Registered the pre-outcome Qwen3.5 dose-grid recalibration on doubt-snap-cross-family (commit 8aa1dc02 on exp/doubt-snap-cross-family): per-cell FIT grids 4B {10,20,30,40,50,60,75} / 9B {60,80,100,120,140}, selection rule and thresholds unchanged, A10G operational change folded in. User approved the paid FIT-sweep-only Modal relaunch (~$1-3/cell); relaunch executor dispatched to verify volume artifact reuse and launch both cells at batch 1. Rep-2 multisource scaffold completed: 221 fresh confabs (139/6/76 across three sources), G0 mining floors pass, 8-row smoke green with RunLog per-row persistence confirmed; awaiting rebase onto main + gate text + predictions + sign.
- next steps:
  - Report relaunch app IDs; then rep-2 sign flow (rebase, gate text to user, both predictions, sign, launch on 3090).
### 015-result - Rep-2 multi-source layer contrast: FULL PASS, resolved, PR #264

- at: `2026-07-10T01:25:26Z`
- kind: `result`
- summary: Rep-2 resolved FULL PASS on the multi-source pool: hs29 92.76% vs hs34 73.76% (+19.0pp), paired McNemar 42:0 discordants p=4.5e-13, G2' +1.43pp, G3' interpretable at 73.76%. Red-team reproduced every number from per-row RunLog; lead re-derived the paired table; two disclosures registered (hs29 absolute cost doubling; 179 distinct normalized questions among 221 rows, verdict invariant). Both scoreboard predictions correct. Pairs with rep-1 as the pool-sensitivity story: magnitude unidentifiable near ceiling, replicates off-ceiling with the same frozen instrument. PR #264 open. Qwen3.5 Modal dose sweeps still in flight.
- next steps:
  - Merge PR #264 after user review; adjudicate Qwen3.5 dose selections when Modal reports; then revise cross-family layer contrast to consume validated ceiling-robust gates.
### 016-result - Qwen3.5 recalibrated sweeps: both cells G0 null, family-level no-window finding

- at: `2026-07-10T07:56:02Z`
- kind: `result`
- summary: Both recalibrated Qwen3.5 FIT dose sweeps committed selected_dose null. 4B: coherent tighten peaks ~33% at dose 40 then JSON-corruption collapse (well-formed 90%->55%->3% across 40/50/60); 9B: peaks ~6% near 140-150 before the 200 cliff. Well-characterized no-window nulls, not grid artifacts: the doubt-gated caution snap does not transfer to Qwen3.5 at registered thresholds (vs 73.5% held-out on Qwen3-4B). Both cells ineligible-before-held-out for the cross-family denominator. NOTEBOOK entry committed on exp/doubt-snap-cross-family.
- next steps:
  - Present resolve-time adjudication options for the cross-family panel eligibility arithmetic to the user; remaining panel cells proceed.
### 017-decision - Qwen3.5 nulls decomposed: regulation transfers, format breaks; 4B-local mid-band next

- at: `2026-07-10T10:52:21Z`
- kind: `decision`
- summary: Row-level decomposition of both Qwen3.5 null cells reframed the finding: 9B doubt-write actuates stated-confidence refusal on 886/912 fired confabs at dose 200 (format-agnostic 'refused' flag) but strictly entangled with JSON corruption (well-formed 2/912); 4B peaks at ~39% refusal even format-free before total degeneration. User adjudication: strict JSON was partly a parseability holdover; the honest framing is 'regulation works, format breaks' for 9B, weak-actuation for 4B. Verified the old forced-fill issue is triple-guarded now (min_new_tokens=1 + EOS, baselines natural-stop 99%/98% at 69/102 avg tokens, clean_tighten requires natural stop). Flag quirk noted: 4B dose_50 semantic_refuse (142) > refused (115). DECISIONS: (1) anchor-placement audit (read-only, free) is the last unchecked harness surface; (2) refusal/coherence decomposed readout gets governed provenance inside (3): a new exploratory amendment testing whether a J-space mid-band write site on Qwen3.5-4B decouples refusal from corruption, run LOCALLY on the 3090 per user (stronger finding if the weakest cell rescues; free lane). Requires Qwen3.5-4B J-lens profile (band is model-specific), fresh mid-band captures/fits from doubt-snap FIT rows, small dose ladder with collapse diagnostics.
- next steps:
  - Dispatch anchor audit + scaffold qwen35-4b-midband-doubt-snap amendment in a new worktree (draft, profile as pre-sign prep, no sign without user).
### 018-infrastructure - Tuner lines reunified (PR #142); doubt-snap branch merged (PR #265)

- at: `2026-07-10T11:02:40Z`
- kind: `infrastructure`
- summary: Merging the doubt-snap branch surfaced a diverged submodule pin: exp branch at 9a97540 (batch verbs, HF-token loaders, batched steer) vs main at cd30d482 (RunLog, redaction, dose calibration), neither containing the other. Resolved by merging the tuner lines: Synaptic-Tuner PR #142 (one additive conflict in MechInterp/cli.py, both helper blocks kept; 206/206 tests pass) -> tuner main 86b134c. Repo submodule repointed to 86b134c in the merge commit; PR #265 (Qwen3.5 dose recalibration + characterized no-window nulls + Modal durability/operational fixes) merged to main. All future pins get RunLog + batch/steer verbs together. User approved the tuner merge explicitly after a classifier lift.
- next steps:
  - PR #264 (rep-2 full pass) still open awaiting user review. Anchor audit + mid-band scaffold agents in flight.
### 019-decision - Standing directive: local GPU runs move to pinned Docker images

- at: `2026-07-10T12:57:38Z`
- kind: `decision`
- summary: User directive (2026-07-10): moving forward all local 3090 experiment runs use the Docker method, never bare shared conda envs. Trigger: unsloth_env silently aged out of model_type qwen3_5 (transformers too old), forcing a documented mid-experiment env hop to base conda; file instruments are sha256-pinned in experiment.yaml but the runtime was not, an asymmetry in the provenance story; Modal lane already containerized. Implementation queued: (1) generic mechinterp runner image in synaptic-tuner (CUDA + torch + pinned transformers + flash-linear-attention, digest printed at run start) via tuner branch+PR; (2) mechinterp-cells skill invariant in canonical .skills/: local GPU runs execute in the pinned image and experiments record the image digest in instrument.pins; delegation prompts restate it. Exception honored once: qwen35-4b-midband-doubt-snap finishes on its documented deviation; containers bind at the next experiment boundary.
- next steps:
  - Builder dispatched for the tuner Dockerfile PR + skill-invariant PR.
### 020-checkpoint - Checkpoint

- at: `2026-07-10T14:15:52Z`
- kind: `checkpoint`
- summary: Midband Stage A+B lead spot-check PASSED (build_manifest per-layer AUC/tau/sigma_c match report; reused_rows_manifest strictly ID-only; provenance pins verified). RunLog deviation for Stage A adjudicated ACCEPTABLE (per-layer JSON flush provides the crash-resume property at the loop's natural granularity); ruling to be recorded in experiment NOTEBOOK by the Stage C builder. Fresh stagec-builder agent dispatched to write and smoke run_dose_ladder.py (RunLog per-row, registered decomposed readouts, grader mirrored verbatim from doubt-snap cross-family) before sign. Docker lane closed out: mechinterp-runner:local built green (numpy 2.2.6 / sklearn 1.7.2 Python-3.10 caps), lead GPU smoke in-container passed (CUDA on 3090, qwen3_5 config parses, provenance JSON emitted); both branches pushed and PRs opened UNMERGED for user review: Synaptic-Tuner #143, EHR #266.
### 021-checkpoint - Checkpoint

- at: `2026-07-10T14:46:48Z`
- kind: `checkpoint`
- summary: User approved and lead merged all three open PRs: Synaptic-Tuner #143 (pinned mechinterp runner image, CUDA 12.8.1/torch 2.9.1/transformers 5.12.1), EHR #266 (Docker local-lane skill invariant), EHR #264 (rep-2 j-space layer-contrast FULL PASS evidence). Repo main now at 618b62bc; tuner submodule pin unchanged at 86b134c (no pin bump needed; future experiments adopt the runner image from tuner main). Docker directive is now fully on the record in skills; the qwen35-4b-midband cell remains the one honored env-deviation exception.
### 022-checkpoint - Checkpoint

- at: `2026-07-10T14:58:11Z`
- kind: `checkpoint`
- summary: qwen35-4b-midband-doubt-snap SIGNED after Stage C builder delivered run_dose_ladder.py (smoke PASS: readback within 0.3%, natural stop, RunLog resume verified zero-regen; 3 registered arms x 4 layers x 7 doses = 84 cells + shared baseline, ~74,750 generations). Predictions registered pre-outcome: user G1-passes (decouples), orchestrator G1-passes (hs23, 6-12 sigma). Grids/floors locked (refused>=60% AND well_formed>=80%, known false-refusal<=10%). Sign gap caught and fixed: bin/exp sign pinned only the scaffold's 5 instrument files; the 3 Stage C modules added to modules+pins by hand (sha256) pre-launch, recorded in experiment NOTEBOOK. Launch plan user-approved: batch probe (16/32 with semantic parity vs 8) then full ladder on the free 3090; dispatched to stagec-builder. Also this segment: user approved and lead merged tuner #143, EHR #266, EHR #264.
### 023-checkpoint - Checkpoint

- at: `2026-07-10T15:24:06Z`
- kind: `checkpoint`
- summary: Stage C batch probe + launch (stagec-builder report, lead-verified process live): Qwen3.5 batch-composition non-determinism CONFIRMED on the local 3090, not just Modal A100s -- at bs=16 and bs=32 vs the bs=8 reference (n=30 rows, hs23, dose 8 sigma), most divergence was wording drift but one row (kuq_unknowns_all:1041, gated arm) categorically flipped refused=True/clean_tighten=True at bs=8 to a substantive answer at BOTH 16 and 32, i.e. batch size flips primary G1 gate metrics. Fallback rule applied: full ladder launched at batch 8, 2026-07-10 11:20 local, harness-tracked, pinned-file hashes verified byte-identical pre-launch, probe scratch cleaned. Revised runtime ~48-55 h (74,753 generations; measured ~1.7-3.5 s/row by arm). Run order: shared baseline then per layer (20->23->26->30) gated+permuted_gate then random_direction, all doses per RunLog file; resumable per dose|row key.
### 014-checkpoint - Checkpoint

- at: `2026-07-10T19:19:39Z`
- kind: `checkpoint`
- summary: PR #258 (experiment provenance reorganization) MERGED after full audit + remediation arc. Fable-tier audit verified: all 40 legacy amendments migrated with verdicts/gates/numbers byte-preserved, 45/45 run records archived, no new data exposure, nothing stranded on the Windows-side worktree (identical to PR head, clean). Blocking findings fixed by remediation: 7+44 dangling evidence pointers in governed docs corrected against the audit census, 23 stale historical pins re-pinned (+3 more surfaced by the main merge) with NOTEBOOK provenance entries, exp validate extended to gate historical-status pin drift, main merged with 5 conflicts resolved (mechinterp SKILL.md restructure kept both invariant sets; session notes renamed to timestamped scheme with checkpoints preserved and renumbered). Post-merge: validate OK (60 experiments) on main. Session-note tooling now uses the timestamped path (this checkpoint is the first at the new path).
### 015-checkpoint - Checkpoint

- at: `2026-07-10T21:49:59Z`
- kind: `checkpoint`
- summary: Paper 4 revision arc executed and merged: reviewer memo recovered from agent transcript and committed (docs/review/paper4-two-signal-readout-review-2026-07-10.md); PI approved full plan incl. veto requalification + logprob baseline. paper4-revisor (fable) executed all 8 memo items, lead-verified against AM/AP/rep2 amendment docs, merged dcfa6634. Intro citation anchors added f9da0ba8. PRs merged: #269 (Amendment Z Z-G3 gate-wording erratum, notebook-tier), #270 (dial logprob baseline NOT computable from cache: extraction never recorded logits; teacher-forced CPU/GPU re-forward deferred until midband ladder frees the 3090). VOICE.md gained binding 'Synthesis, not journey' section (PI directive): superseded numbers never on the page, predictions/gate-misses as compact registered facts, process narration only in AI-workflow methods. Synthesis pass dispatched to paper4-revisor: remove 0.980 veto number entirely (confounded per AM/AP; honest ~0.74 controlled core is the finding), de-narrate confound-hunt arcs. Queued for same pass: related-work readability (PI reading feedback: section 2 blocks open with apparatus not question, and argue our +0.065 inside related work; fix = plain-language question openers, our numbers out of section 2). Midband ladder healthy: hs20 arms done through permuted_gate, into gated dose_12, GPU 55%.
### 016-checkpoint - Checkpoint

- at: `2026-07-10T22:28:01Z`
- kind: `checkpoint`
- summary: Paper 4 editorial arc continued through three more PI-directed passes, all lead-verified and merged: (1) synthesis pass (0.980 removed from all sites incl. a rhetorical-foil survivor the lead caught; 4.4 rewritten as decomposition statement; U overshoot story dissolved, controlled core sits inside registered band; Figure 5 rebuilt from generator; lead adjudication 91722d5a scoped 4.3 decomposition attribution to raw base as explicit inference). (2) related-work pass (section 2 question-first rewrite, our numbers out of related work, steering block reduced to one scoping sentence with substance consolidated in section 6; merged 95bff4ae). (3) self-containment + headings pass (body prose freed of amendment codenames/doc filenames/slugs/PR numbers/repo paths, provenance consolidated to Appendix A with 7 new verified rows; ~25 bold run-ins converted to real subheadings; lead fix 959603d5 promoted section 3 setup blocks to ###; merged e0c833d9). VOICE.md gained three new binding sections this arc: Synthesis-not-journey, External-facing self-containment, real-headings structure habit. TODO backlog: CD (correctness-direction rotation tracking, upgrades dial cold-transfer inference to measurement) + LP (logprob re-forward), both gated on midband ladder freeing 3090. Forward note: companion-paper reference should switch to paper 3's own identifier when it exists. Revisor on standby for further PI reading feedback.
### 017-checkpoint - Checkpoint

- at: `2026-07-10T23:54:42Z`
- kind: `checkpoint`
- summary: H9 feasibility adjudicated: NOT computable from cache (AL fit on full 1,662-row surface, no held-out split; in-cell OOF 0.6802 recorded as gate-setting prior); memo committed e1ec09bb, H9 backlog row now CPU+GPU, scout dispatched on held-out candidate-list recoverability (union 18,496 minus fit 1,662). Answered PI question on doubt+propensity combination: parallel mirrors (AC doubt, AO propensity, AN selector) plus ONE additive two-sensor controller g_i=-a_d*z_d+a_p*z_p in draft exp two-signal-caution-regulation-instruct, killed at calibration, collapsed to doubt-only gate in tighten; no serial confab-through-doubt routing exists. Worktree/branch audit run: two-signal AMENDMENT.md+experiment.yaml were UNTRACKED disk-only, now committed+pushed on their branch (was never pushed); Amendment Y-thinking draft stranded on amendment-y-thinking-readout branch (absent from main, never migrated); AK worktree holds uncommitted ak_stage2 G3 report + row-level pull data; steering-cell skill branch never merged (mechinterp-cells likely supersedes); old amendment branches (AE/AG/AH/AB/AC/R/Y-base) verified MIGRATED to experiments/ on main, stale; jspace replication/localization branches stale (main ahead, resolved). Next: PI decision on stranded drafts + stale-branch cleanup sweep.
### 018-checkpoint - Checkpoint

- at: `2026-07-11T00:31:59Z`
- kind: `checkpoint`
- summary: Editorial + hardening batch progress. Paper 3 anatomy pass verified+merged (c2e977b2: doubt=answerability-gate identity, caution trained-only caveat as finding, propensity one-line pointer, A3 move-out, self-containment). Paper 2 voice pass verified+merged plus 3 lead adjudications (b781f937: abstract KTO seed count corrected to two analyzed seeds per amendment_a_selfaware_summary.csv, grammar, ranking-signal scoping). Steering-cell salvage merged (PR #271: smoke-first+SHA-pin discipline, gate-primitive logic, PEFT/layer-offby-one/ULP gotchas into mechinterp-cells); Y-thinking draft archived (5da6587d); both retired branches await explicit PI deletion OK. H9 SIGN-OFF: PI prediction recorded = G1 INCONCLUSIVE band (f9e7c995); PI approved sign + HF staging + Modal spend cap $15; h9-designer wiring scripts + FID smoke (d_raw hard target adjudication confirmed; note designer correctly identified AL=radial-anti-propensity-steering, not selected-setpoint-regulator which is AN). New backlog row TS: steering-under-thinking cell (does gated caution write change the CoT; reuses archived cot_confidence rubric; after H3/H4). PI directive: draft H3/H4/H6/TS with placeholders NOW; two designer agents dispatched (a: H3 exp/h3-snap-seed-decode-replication + H4 exp/h4-ungated-dose-matched; b: H6 exp/h6-genstream-hook-check + TS exp/ts-steering-under-thinking). Ladder: hs20 gated dose_20 320/882, ~3.8s/row, GPU 26%/9GB/60C, no crashes, ETA ~2 days. Next: verify 4 drafts, red-team H9 instrument post-wiring, sign, stage checkpoint, Modal launch.
### 019-checkpoint - Checkpoint

- at: `2026-07-11T03:42:12Z`
- kind: `checkpoint`
- summary: H9 cloud run arc complete. Attempt 1 reaped (undetached client exit, operator error). Attempt 2 crashed at extraction start (ModuleNotFoundError: fresh clone lacks the untracked legacy probe tree the local checkout has). Instrument repair 2 = bin/exp repin FIRST PRODUCTION USE: install legacy-wrapper-tree at experiment/phase1/probe, shim renamed AC config (prompt.system verified byte-identical across rename d55b7d26), PYTHONPATH, fail-fast import preflight before model download; rehearsed green in a clean pinned-commit checkout; commit b4b68ef0. Attempt 3 completed BOTH GPU stages (500/500 extract, fidelity spot-check 0.0; 500/500 generate) then crashed at harness step 4b reading gen/rows_graded.jsonl where the entry script writes gen/rows.jsonl; stage trees lost because checkpoints were top-level-only; app stopped to cut retry spend. Repair 3 = filename fix + in-run tree mirroring + restore-on-start resume (unit-tested; repin 844f4c7b; commit 58e598c7). Attempt 4 ran clean end to end: preflight OK, extract OK, generate OK, DONE marker on volume. Spend ~2 USD of 15 USD cap. Next: pull ckpt/h9-holdout-r1, run signed score_holdout.py, adjudicate locked gates (PI prediction: G1 inconclusive band). Durable lesson: CPU smokes never execute the cloud harness post-stage plumbing; in-run tree checkpointing caps the cost of such bugs at one stage.
### 024-checkpoint - Checkpoint

- at: `2026-07-11T10:20:27Z`
- kind: `checkpoint`
- summary: H9 RESOLVED: INCONCLUSIVE-BY-POWER, PR #273 open. The enlarged read-once adjudication on the 750-row draw: the +250 registered enlargement (RNG continuation, replay hard-asserted line-identical to the committed 500 manifest, largest-remainder allocation 113/69/20/17/12/11/8, 0 near-dups flagged) added ZERO confabulations - 4 total in 605 unanswerable rows, 601 honest refusals - so H9-G0 stays unmet and per the pre-registered remedy text no further enlargement is permitted; G1 never read. G2 caution control passed both reads (0.9734/0.9702): pipeline certified, confab scarcity is real behavior (AI-TRUE refuses 99.3 percent of held-out unanswerable rows vs ~91 expected from fit-surface rates, plus 30/97 knowns). Verdict + scoreboard adjudication in AMENDMENT.md section 10 (PI's INCONCLUSIVE call closest; orchestrator's G0-met call wrong). The repair-3 resume machinery made the enlarged pass cost 603 GPU-seconds. Total spend ~2 USD of 15. TODO H9 row closed with the follow-up note: any future propensity gate needs a surface where the checkpoint actually confabulates (weaker checkpoint or adversarial pool), not more rows from this one. Paper 5 consequence recorded: the read half of 'reads but does not actuate' keeps the in-cell OOF 0.6802 label; no registered held-out number exists. Local 3090 ladder meanwhile: hs20 complete, hs23 gated mid-run (interim: hs23 notably weaker than hs20 - 13/27/36 percent vs 21/46/59 at doses 2/4/6), hs26 pending, ~1 day to finish. Remaining follow-ups: KG-ingest of the H9 verdict (librarian, post-merge), PR #273 merge, H3/H4/H6/TS wiring.
### 025-checkpoint - Checkpoint

- at: `2026-07-11T14:00:59Z`
- kind: `checkpoint`
- summary: BB resolved: base propensity read certified. Phase 1 ran clean on Modal (3,447 s A10, ~$2; one aborted empty-HF-token launch caught inside a minute). Pre-launch: full red-team (1 invalidating finding, missing degenerate/schema_valid guard on the contrast cells in fit+score, fixed and regression-locked, smokes 14/14; FID-2 gates.yaml repin 3f23b51f->33fe08ad adjudicated intent-preserving), two lead adjudications recorded pre-read (gradeable guard scope; G2 gradeable-only primary). Results: G0 205 confabs/1,020 refusals on guarded 1,662-row base fit surface; read-once gate on vendored 750: BB-P1-G1 PASS AUROC 0.8179, CI [0.7190, 0.9042]; G2 caution 0.9820; FID-1/2 pass; near-dup 0 flagged. First certified propensity reading in the program, zero training. Resolved; PR #274 open; TODO BB updated (half c, base actuation, remains). Gotcha: modal CLI 1.5.1 volume get fails Errno 21 on directory trees; use Python SDK iterdir/read_file with skip-existing resume. KG-ingest queued post-merge.
- next steps:
  - PR #273/#274 merges; ladder completion -> aggregates -> red-team; then H3/H4 lane; BB half c amendment after snap hardened
### 026-checkpoint - Checkpoint

- at: `2026-07-11T21:58:59Z`
- kind: `checkpoint`
- summary: Mistral probe-cell crash diagnosed and repaired pre-sweep: the in-pipeline gen-stream smoke probe was tied to max(dose_grid), so mistral's sigma-mapped grid [6..27] made the probe inert (byte-identical output at strength 27, equal to the strongest arm) and the guard refused launch. This falsifies sigma-ladder transfer for mistral (inert at 29 sigma where llama responds at 5-13 sigma). Morning artifacts bracket mistral's window empirically: inert at 27, fully degenerate at realized strength 106.5 (584/584 fired confabs at dose 100), tokens moving at 250. Fixes on exp/doubt-snap-cross-family commit b8e9c873: mistral grid revised pre-sweep/pre-outcome to log-span (27,100) = [30,38,46,56,67,80,92]; smoke probe decoupled to fixed 250.0; dated AMENDMENT extension + NOTEBOOK entry + pin refresh (no-further-grid-changes clause never triggered because the selection rule was never evaluated on [6..27]). Mistral relaunched detached batch-1 (app ap-WQXHAMrCooWjpskPgy36cH), weights loading, background poll armed. Skill PR #275 updated (cffaed77): rule 4 now requires empirical per-cell bracketing (sigma-mapping is a first guess only); rule 6 gains the probe-decoupling gotcha. Llama sweep live and healthy: real interior dose-response, fired-confab clean_tighten 64->107->61 across strengths 5.3->9.1->12.4 then collapse, peak ~18.5% well below the 0.60 selection floor, trending toward an honest FIT dose-viability null. Local 3090 midband ladder: baseline + hs20 all arms + hs23 gated/permuted complete; hs23 random_direction on dose 6 of 7 (~93%); hs26 and hs30 late-comparator cells remain (roughly a day-plus).
### 027-checkpoint - Checkpoint

- at: `2026-07-12T14:21:18Z`
- kind: `checkpoint`
- summary: jspace-family-atlas full arc closed in one day: signed (2524891) with both predictions registered pre-launch (orchestrator and user both holds-on-both), launched with user approval (Modal ap-q2mU3RZwwrHyaTbr1ehwVm, $10 cap, ~$2 actual), resolved, PR #277 opened. Gates AG0/AG1/AG2 PASS with lead re-derivation from pulled captures. Prediction NOT MET both families (eff_dim_frac peaks early, 0.14/0.09 depth, not interior); falsifier not triggered (non-monotone profile, readable interior band). Layer map delivered: llama ~L20-23 (raw refusal 0.90), mistral ~L15-17 (0.925). Red-team pre-verdict: fleet-audit 0.997-vs-0.90 reconciled as population definitions (refused-vs-known vs pooled-answered); random-direction control committed showing refused-vs-known norm confound (random up to 0.97) while caution/raw-refusal baselines stay 0.5-0.75. Exhaust-skill-builder assigned fleet HF dataset dry-run build (no upload; card for user approval). hs30 ladder comparator still running locally.
- next steps:
  - Merge PR #277 on user OK; hold fleet resolve for hs30; review builder's dry-run card; draft raw-refusal-axis actuation amendment using the atlas layer map
### 028-checkpoint - Checkpoint

- at: `2026-07-12T15:00:25Z`
- kind: `checkpoint`
- summary: Atlas arc fully closed: PRs #277 (jspace-family-atlas resolved) and #278 (family-atlas skill + docs/atlas/family-layer-map.md registry) MERGED with user approval; KG ingest committed and lead-verified (6f09ec14: experiment node + 2 mechanisms - workspace-band-peak-location-is-family-relative, refused-vs-known-contrast-carries-norm-position-confound; validator 0 errors, manifest kg: list filled, exp validate OK). PI directive made standing: atlas extraction is the STANDARD for every new model/family/size before actuation design; axes assumed universal, layer band family/size relative, no cross-family layer porting. Doc janitor pass: TODO.md gained the dated 2026-07-12 arc section (fleet/ladder/atlas/skill/raw-refusal candidate/HF backfill rows) + index regen; AGENTS.md (canonical) skills list completed to all nine and synced into CLAUDE.md (gotcha: CLAUDE.md orchestrator section is GENERATED from AGENTS.md, first edit got reverted by sync). Two finds lifted to PI: 7 untracked aux-head-era docs (pr118-120 reviews/prep) awaiting commit-or-archive call; untracked experiment/ tree holds ~100GB local Phase 1 run products on canonical - no action without deliberate curation. In flight: exhaust-builder fleet HF dataset dry-run card; hs30 ladder arm.
- next steps:
  - hs30 lands -> fleet resolve Outcome + ladder aggregates; review exhaust dry-run card with PI; draft raw-refusal-axis actuation amendment on the atlas layer map; PI call on aux-head doc strays
### 029-checkpoint - Checkpoint

- at: `2026-07-12T16:04:53Z`
- kind: `checkpoint`
- summary: Phase 1 outputs migration EXECUTED (commit 30fa503e): the untracked ~99GB experiment/ tree scouted (read-only inventory: 97.5GB unique research data, ZERO duplication vs 9.8MB code-only archive, bridge containment confirmed ABSENT locally, no tracked references), user approved the two decisions (shared bulk to gitignored archive/experiment/phase1-data/, 3.7MB junk deleted), migrator built a deterministic classifier (letter-to-slug from registry.json legacy.label, 40 mappings, flagged-not-guessed on amendment_a_*/mi_* dirs) with dry-run manifest which the lead reviewed and executed: 317/319 entries, 43.9GB to experiments/<slug>/analysis/phase1-migrated/ (SR 26GB, Z 8.6GB, AH 6.7GB), 56GB shared to phase1-data, exp validate OK post-move. Two Amendment AI PAR eval dirs hold 14 Docker-era foreign-UID files: copied byte-verified to experiments/probe-as-reward, source residue (5.4MB) awaits operator sudo rm. Gotcha: shutil.move copy-fallback rmtree dies on foreign-owned entries; pre-move ownership scan (find ! -user) belongs in bulk-move scripts. Aux-head doc strays (7 files) still await PI commit-or-archive call.
- next steps:
  - PI runs sudo rm -rf experiment residue; hs30 -> fleet resolve + raw-refusal draft; exhaust dry-run card review
### 030-checkpoint - Checkpoint

- at: `2026-07-13T02:53:31Z`
- kind: `checkpoint`
- summary: Ladder + fleet both RESOLVED same night. hs30 ladder completed 22:35 (74,753 generations, ~59h wall, bs=8, clean exit). Lead recomputed headline aggregates from raw RunLogs pre-red-team (matched runner exactly); red-team over seven attack surfaces returned G1 SURVIVES, no invalidating finding; three lifted adjudications accepted (240-known cost denominator with 10/13 fired-known conditional reported alongside; in-sample FIT-only scope; official summary promoted to analysis-committed). qwen35-4b-midband-doubt-snap RESOLVED: G1 PASSES at hs20 dose 8x sigma_c, the unique cell in the locked 4x7 grid (refused 0.684, well-formed 0.980, known false-refusal 0.042); falsifier does not fire; late comparator hs30 reproduces entangled failure in-grid; layer potency monotone toward earlier layers (hs20>hs23>hs26>hs30), echoing the atlas early-structure finding; PR #279. Red-team scope notes adopted verbatim: selectivity belongs to the c_hat write direction not the gate (permuted confabs refuse 0.669 vs gated 0.684; dosed knowns only 0.056); placebo magnitude-matched via readback; no optimum claim (hs20 is grid-edge, earlier layers untested). Fleet doubt-snap-cross-family-confirmatory then RESOLVED: NOT PROMOTED, prediction not met (uniform pre-outcome G0 dose-viability stops, peaks 0.326/0.184/0.000/0.058), falsifier wording gap recorded straight (binds held-out fails only); Outcome indicts the universal 0.94-depth write-site rule via c_hat audit + same-substrate ladder contrast (0.326 late vs 0.684 mid-band); both scoreboard predictors wrong on the fleet, both right on the ladder (orchestrator wrong on layer: hs20 not hs23); PR #280. Both PRs await user merge approval. KG ingest queued post-merge for both.
- next steps:
  - User merge call on PRs #279/#280; KG-ingest both resolves post-merge; draft raw-refusal-axis actuation amendment (atlas layer map sites, exterior-shaped prediction/falsifier); review exhaust dry-run card; sudo rm residue + aux-head strays still pending PI
### 027-result - H4 resolved all-gates-pass (PR #281); H3 signed; H6 launched then bounced on two harness bugs

- at: `2026-07-13T11:16:48Z`
- kind: `result`
- summary: H4 red-team survived all five surfaces; Outcome written with two binding scope statements (60.1% is damage not refusal, decomposed 55.8pp false-refusal + 3.9pp wrong + 0.4pp degenerate, superseding the n=80 36.2% diagnostic; gate-supplies-selectivity bound to Qwen3-4B/L34/dose-200 and reconciled with the ladder permuted-gate result as operating-point dependence). Resolved, anchor checksums recorded, PR #281 open awaiting user merge approval. H3 signed after accepting all six builder adjudications (decisive: G3 placebo re-draws decode greedy, thresholds anchor to greedy precedent; Lane phrase sampled placebo arms adjudicated a drafting slip); six modules sha256-pinned by hand since exp sign pins configs only; evening 3090 slot. H6 launch-time resolution committed (revision 64033659, direction sha 9e0bf40c, 25-ID pool; scout report corrected twice: staging rows.jsonl has no question text, text lives in pools/ak_stage1_pool.jsonl; 328 unique keys not 25) then both paths failed on harness plumbing: tuner device mismatch at evaluate_g2 (direction on cpu), bespoke pre-flight assert that may conflate readback misconstruction with the registered hook-does-not-fire prediction; unsloth also silently redirected the load to qwen3-4b-unsloth-bnb-4bit. Fix reassigned to h4-builder (h6-builder lane stalled behind the idle guard twice). RR raw-refusal design dispatched to fresh agent rr-drafter (heldout-drafter also guard-blocked): keeps doubt-gate arm per H4, atlas sites, Wilson gates, outcome-shape coverage, draft-only.
- decisions:
  - H4 verdict adjudicated by lead; H3 placebo-decode ambiguity adjudicated greedy pre-launch; H6 pre-flight-vs-G1 conflation flagged as an adjudication the fixer must record, not silently fix
- next steps:
  - h4-builder fixes+relaunches H6 (free 3090); lead launches H3 after H6 frees the card (GPU smoke first to calibrate throughput); rr-drafter delivers RR draft; H4 KG-ingest after PR #281 merges
### 028-result - H3 G1 falsifier-fires pending red-team; H4/H6 merged+ingested; RR signed, staged, launch blocked on anchor-slice

- at: `2026-07-13T15:20:47Z`
- kind: `result`
- summary: H3 confirmatory run completed all four phases (443 greedy + 2215x3): G0 PASS (greedy reproduces 73.5%/3.1% exactly), G2 PASS (sampled cost ~6% per-sample), G3 PASS (placebo re-draws robust all 5 seeds), G1 FAIL by collapse: pooled sampled majority-vote conversion 140/925=15.1% Wilson [13.0,17.6] vs 63.5% floor, all seeds fail individually, any-vote 53.2%, mean per-sample fraction 22.0%. If certified, the falsifier fires and the 73.5% headline re-scopes to one greedy decode (write dominates argmax, not the sampled distribution); BOTH scoreboard calls wrong. Verdict withheld pending ladder-red-team instrumentation pass on the batched sampled path (H6 lesson: silent hook non-delivery produces exactly this signature; surfaces: per-row readback in run_log_sampled, fired-vs-non-fired contrast, sampling config echo, batched termination/grading parity, independent majority-vote recompute). H4+H6 PRs #281/#282 MERGED on user approval; KG-ingest done (ac24f7db, 5 new nodes, operating-point reconciliation woven not contradicted). RR: signed with predictions (user: both families shape A; orchestrator: exactly one, lean mistral); harness built (c12e0578, 33 CPU tests) and lead-reviewed, all 7 builder adjudications accepted; lead repaired four sign-surviving cell.yaml placeholders via repin (revisions lead-verified vs fleet SSOT); stager landed row pools + full-depth atlas captures (coverage 1.0 both families, sha-verified); llama launch bounced on missing anchors_at_candidate_layers.json whose GPU-capture-deferred premise is false (staged tensors carry anchor__L0..L28 full depth; pure CPU slice) - fix + relaunch with h4-builder.
- decisions:
  - H3 falsifier verdict deliberately withheld until instrumentation is adversarially verified (adopt-no-null-from-uncertified-instrument, the AK/H6 rule); RR precondition-report naming quirk left as-is (cosmetic, pinned module)
- next steps:
  - ladder-red-team H3 verdict -> adjudicate -> Outcome (falsifier straight if sound; artifact diagnosis if not) -> resolve -> PR; h4-builder anchor-slice fix -> llama then mistral RR cells; session tasks: HF backfill card still owed (task 24)
### 031-checkpoint - Checkpoint

- at: `2026-07-13T23:06:42Z`
- kind: `checkpoint`
- summary: RR + H3 both resolved in one arc. RR cross-family raw refusal: mistral leg completed shape F (peak hs16/dose12 refused 0.5793 vs 0.60 floor, Wilson straddles), red-teamed and CERTIFIED-NULL with a binding detector-width caveat (97 hand-verified mistral-idiom abstentions at the peak would clear the floor; llama's F is robust to detector width, mistral's is not); falsifier fired (neither family shape A), resolved falsified, PR #285 open awaiting PI merge approval; both scoreboard calls falsified. PI directive recorded: future abstention acceptance criteria include a registered blinded hand-check adjudication lane; RR2 successor drafted (exp/rr2-mistral-adjudicated-refusal, 2f9da6d3): detector v2 screen + blinded symmetric adjudication lane as primary instrument, fixed operating point hs16/dose12, held-out leg only, sign blocked on #285 merge. H3: termination-rule artifact confirmed (764/769 term-only failures, eos-at-final-position, texts are clean refusals), harness fixed to is_terminated_naturally single source of truth (16/16 tests, parity exact 1056/1480 and 130/185), repinned d722811e, pre-fix logs archived; full K=5 re-run on fixed harness passes ALL gates (G1 pooled 69.5 pct vs 63.5 floor, every seed above; G2/G3/G0 identical to pre-fix run; seed-20260710 exactly 130/185 = triple agreement), verdict REVISED to resolved (headline survives sampling), both scoreboard calls correct on corrected instrument, PR #283 back to ready with revised resolve (bba2cee5). Next: PI merges #285 and #283; RR2 sign (needs PI scoreboard prediction); held-out ladder sign + GPU sequence; skill rule for blinded adjudication lane after RR2 design approval; KG-ingest both verdicts post-merge.
### 030-result - Held-out ladder promotes shape A; RR2 resolves falsified on certified placebo fire

- at: `2026-07-14T02:49:12Z`
- kind: `result`
- summary: qwen35-4b-midband-heldout resolved shape A and merged (PR #287): frozen hs20 point transfers to fresh held-out rows, fired-confab refused 872/1286 = 0.678 (Wilson [0.652, 0.703]) vs 0.60 floor, wf 0.977, gated-arm known cost 14/360 = 0.039, random no-op, permuted strictly worse; both scoreboard calls correct. Abstention-grading standard institutionalized (PR #286): frozen detector screen + registered blinded adjudication lane, manifest-before-grading and hash-before-unblinding in code, falsifier closes the regress. RR2 (rr2-mistral-adjudicated-refusal-confirm) then ran the full blinded protocol as its reference implementation: context-free agent graded 3582 texts blind (626 TRUE), hash committed pre-unblinding. RG1 PASS 911/1303 = 0.699 [0.674, 0.723] wf 0.987 (both pre-registered bands hit; RR detector-width caveat vindicated, the idiom-inclusive refusal is real with pristine cost 2/382). RG2 PASS. RG3 FAIL: baseline confab adjudicated abstention 0.280 vs random_direction 0.354, +7.39 points vs the 2-point tolerance; the wide instrument reveals 28% undosed baseline abstention the narrow detector read as ~0. Red-team certified the fire across five surfaces (decisive: 435-decoy audit, 255/255 clear-negative agreement, conservative on positives; 160-row baseline re-read 2/160 disagreements both widening the delta; random-arm excess is genuine well-formed hedge content). Resolved falsified as registered, no rescoring lane; both shape-A scoreboard calls incorrect on the verdict while nearly exact on the benefit level. PR #288 open, merge held for user approval.
- decisions:
  - Falsifier fire CERTIFIED, verdict falsified as registered; gated lift +41.9 points (5.7x random) noted as interpretation only, RG3 is a tolerance test not a ratio test, goalposts stand. Forward rule recorded in the Outcome: any successor registers its placebo tolerance (or a pre-stated effect-ratio gate) against the wide-instrument baseline before new data, as a new signed amendment.
- next steps:
  - User merge decision on PR #288; KG-ingest RR2 verdict post-merge; possible successor design note needs user sign-off; HF exhaust backfill (#24) now includes H3/RR/heldout/RR2 candidates.
### 031-result - Calibration study resolved: family-graded wide baselines; qwen placebo suppresses

- at: `2026-07-14T12:38:29Z`
- kind: `result`
- summary: abstention-wide-instrument-calibration ran end-to-end in one day, CPU-only: signed with detector v2 byte-identical to RR2 pins, 31,620 rows staged, 11,788-core blinded pool across 17 cell-scoped shards, seven context-free graders, manifest-before-grading and hash-before-unblinding held throughout. Mid-run instrument correction (H3-pattern, repinned, red-team-verified): attempt-1 opaque ids collided across (hs_index, dose) in the QL ladder cell; blinding and per-line grades unaffected; join corrected to positional. QL cell voided terminally per registered CG1 second-failure rule (two independent graders failed the same 14-decoy clear-positive draw at 0.286/0.429; ten other QL shards passed 0.692-0.929); reported straight as narrow-only. Red-team CERTIFIED-MEASUREMENTS with bit-for-bit recompute. Certified table: qwen wide baseline 0.104 [0.089,0.122], llama 0.164 [0.146,0.184] (lower bound due to unknown_refused carve), mistral 0.280 cited; undercounts 6.1/12.9/12.2 points. Headline surprise: qwen paired placebo delta is NEGATIVE, -5.13 points wide (0.108 to 0.057, non-overlapping CIs) where mistral recruits +7.39: placebo response is family-specific in SIGN. Falsifier adjudicated not fired on the signed consequent-coherent reading (an absolute reading would assert program-wide perturbation-recruited hedging that the suppression contradicts); red-team independently recommended the same. Prediction not cleanly confirmed: placebo near-no-op leg missed in magnitude, llama band missed at 0.164; scoreboard: user correct on per-family differences and qwen baseline, incorrect on placebo magnitude; orchestrator additionally incorrect on llama. Resolved; PR #289 open, merge held for user.
- decisions:
  - Falsifier reading adjudicated signed/consequent-coherent under red-team certification, not chosen for the scoreboard; QL void reported straight, no third grading attempt; successor design rule recorded: no flat small symmetric placebo tolerance, register against per-family wide baselines with two-sided tolerance or effect-ratio gate; CG1 lesson: pooled or larger clear-positive decoy draws per shard.
- next steps:
  - User merge decision on PR #289; KG-ingest calibration verdict post-merge; abstention-grading skill update (CG1 granularity + decoy-carve coverage lesson) as separate PR; RR2 successor design can now register its placebo criterion against the measured baselines (needs user sign-off); HF exhaust backlog #24 grows by this experiment.
### 032-decision - RR3 pre-run scoreboard calls + Q3 framing (PI + orchestrator)

- at: `2026-07-14T13:22:02Z`
- kind: `decision`
- summary: RR3 (rr3-corrected-placebo-replication, draft on exp/rr3-corrected-placebo) pre-run registrations, stated BEFORE harness build and any run. Q3 framing decided by PI: mistral core verdict is reported as a corrected-criterion re-adjudication of RR2's claim (same test done more intelligently, with the rider as additional data exhaust), not as a fresh confirmatory replication. Scoreboard calls. PI: llama placebo sign NULL (model is old and an outlier in his read); mistral RG1 PASS; mistral fresh random seeds INSIDE the +/-8 descriptive envelope. Orchestrator: llama placebo sign WEAK RECRUITMENT (positive, monotone-in-baseline reading of the calibration sign map: llama wide baseline 0.164 sits between qwen 0.104 suppression and mistral 0.280 recruitment); mistral RG1 PASS; at least one of the K fresh mistral random seeds lands OUTSIDE the +/-8 envelope on the recruitment side while staying below the ~14-pt gate-fail threshold. These get copied verbatim into the AMENDMENT scoreboard at sign-off; no edits after results per the no-goalpost rule.
- decisions:
  - Q3: corrected-criterion re-adjudication framing (PI). Scoreboard calls registered as above.
- next steps:
  - rr3-reviser lands revision -> lead final review -> copy scoreboard calls into AMENDMENT -> harness build -> sign with pins -> lift GPU launch approval to PI.
### 033-launch - RR3 signed and launched on local 3090

- at: `2026-07-14T17:05:58Z`
- kind: `launch`
- summary: RR3 (rr3-corrected-placebo-replication) arc completed draft-to-launch in one day. Draft (opus agent) -> lead revision round (Q1 regeneration kept, Q2 max-over-K, Q4 full grid, Q5 scoreboard slots, +/-8 descriptive envelope, >=25 clear-positive draws, rider dosing of answerable rows with source-field question-type stratification) -> PI resolved Q3 (corrected-criterion re-adjudication framing) and gave scoreboard calls (llama null / RG1 pass / seeds inside; orchestrator counter: llama weak recruitment / RG1 pass / one seed outside) -> harness build (15 modules, 78-test suite, detector v2 byte-identical to RR2/calibration pins, held-back decoy pool, pooled CG1 floor, max-over-K arithmetic proven by test) -> lead fixed the build's STOP item (cell.yaml rider_cells YAML parse error introduced in the revision commit; shared config hoisted to rider_shared), pinned llama revision 006f5dcd (verified RR cell.yaml + fleet model_matrix agree), confirmed K-seeds [30260714, 30260715, 30260716], SIGNED. Paper 5 manuscript updated on main with RR2 falsification + calibration Section 4.8 (cfdc90d7). Calibration KG-ingest committed (06f525b2). LAUNCH: local 3090 (free lane, standing approval, PI also explicitly approved after the auto-mode classifier flagged the --i-know-this-runs-on-gpu acknowledgment flag; PI said proceed). First launch attempt stopped cleanly pre-GPU: staged inputs absent in fresh worktree; fixed by symlinking RR worktree row pools + atlas captures (gitignored row-level artifacts, correct lane). Relaunch passed materialize for both families (mistral 1312/382, llama 2956 joined) and entered fit_reuse RG0.
- run ids:
  - `rr3-pipeline-20260714b`
- commands:
  - `pipeline.py all --batch-size 8 --i-know-this-runs-on-gpu (local 3090, detached, log analysis/pipeline_run_20260714b.log)`
- next steps:
  - On pipeline completion: RG0 byte-repro verify, build adjudication pool, commit pool manifest, dispatch context-free blind graders, hash-commit, CG1, scorer, red-team certification BEFORE verdict. Pending elsewhere: sign-flip analysis amendment draft (#39), abstention-grading skill PR (#42), scale test 1.7B+~9B held for RR3 (#41).
### 034-decision - Sign-flip analysis: pre-run scoreboard calls + structural finding

- at: `2026-07-14T17:50:03Z`
- kind: `decision`
- summary: placebo-signflip-question-type-analysis (draft on exp/placebo-signflip-analysis) pre-run registrations. Drafter's structural finding, lead-verified bit-for-bit from row_level_scored.jsonl: every dosed placebo row in every family/cell is unanswerable (kuq), so the certified cross-family sign difference (qwen -5.13 suppression vs mistral +7.39 recruitment) was measured entirely on the unanswerable stratum and question type CANNOT explain it behaviorally on existing data (it never varied). Powered question-type tests move to the mechanism leg (anchors exist for both types in all three families) and prospectively to RR3's rider. Scoreboard calls (PI then orchestrator): M1 answerable-vs-unanswerable separation on doubt/caution axis in all three families: YES / YES. kuq-subtype concentration of the placebo effect: CONCENTRATED-OR-UNEVEN / EVEN-SPREAD (differentiating slot). M3 realized displacement differs by type: YES / YES. Lead decisions: subtype breakdown extended to mistral; mistral hs16 directions provenance-by-regeneration via RR fit manifest. RR3 pipeline meanwhile mid-generation on the 3090 (92 percent util).
- decisions:
  - Scoreboard registered as above; subtype breakdown extended to mistral; directions provenance-by-regeneration.
- next steps:
  - Harness build for signflip analysis (BG1 exact frame-port acceptance test is the known risk) -> lead review -> sign -> CPU run -> red-team -> resolve. RR3: await pipeline completion notification.
### 035-checkpoint - Pre-restart state: RR3 generating, sign-flip behavioral leg done

- at: `2026-07-14T18:27:53Z`
- kind: `checkpoint`
- summary: PI will restart the machine once the RR3 GPU run completes; session pauses there. STATE AT PAUSE. RR3 (exp/rr3-corrected-placebo, signed): pipeline through mistral core (all 4 arms + 3 seeds) and heldback passes; mistral rider in progress, llama rider remains; log analysis/pipeline_run_20260714b.log; on completion DO NOT dispatch adjudication until resume. Sign-flip (exp/placebo-signflip-analysis, SIGNED, run partially executed): BG0/BG1/BG2 all PASS (BG1 frame port 1303/1303 exact firings, 0/1692 mismatches; BG0 reproduced both certified deltas bit-for-bit). Behavioral leg executed: qwen suppression CONCENTRATED in future-unknown subtype (-24.7 pts, n=190, baseline 0.332) vs -2.8 or less elsewhere; mistral recruitment broad-based positive (+3.8 to +11.8 across all six subtypes); baseline hedging orders subtypes identically across families. PI scoreboard call (concentrated-or-uneven) currently winning vs orchestrator (even-spread); near the registered inert-reading falsifier for qwen; NO verdict yet, red-team required first, mechanism leg (M1/M2/M3) NOT run (deferred for host RAM until GPU job ends). Report at analysis-committed/signflip_report.json, uncommitted. RESUME SEQUENCE: 1) verify RR3 pipeline completed cleanly (RG0 byte-repro in log), 2) run sign-flip mechanism leg (opt-in real-data loaders incl. mistral 251MB / llama 493MB anchor JSONs), 3) rerun report.py, commit report, 4) red-team certification of sign-flip, resolve, PR; 5) RR3 adjudication cycle: build_adjudication_pool, commit pool manifest BEFORE grading, context-free blind graders, hash-commit before unblinding, CG1, rr3_scorer, red-team, resolve, PR. Scoreboards registered in both AMENDMENTs; no goalpost moves.
- next steps:
  - Await RR3 pipeline completion notification; then checkpoint again and tell the PI it is safe to restart.
### 036-checkpoint - RR3 generation COMPLETE; machine quiesced for PI restart

- at: `2026-07-14T19:13:13Z`
- kind: `checkpoint`
- summary: RR3 pipeline exited 0 after the full sequence (materialize both families, fit_reuse RG0 reconstruction, heldback passes, mistral core all arms, mistral rider, llama rider). GPU freed (0 MiB). Runlog artifacts on disk in the rr3-corrected-placebo worktree analysis/runlog/: core baseline 1694 rows, gated 1303 fired (matches RR2's fired count exactly), three random seeds (30260714/15/16), dose_knowns 382, heldback passes, 87 rider files (mistral + llama dose ladders incl. answerable-row legs). Pipeline printed the 5-step adjudication instructions and stopped, as designed; nothing dispatched. Sign-flip behavioral leg done earlier (gates pass, PI subtype call ahead), mechanism leg deferred. NOTHING RUNNING: no background tasks, no agents in flight, both amendment branches committed locally, main pushed. Safe to restart the machine. RESUME: follow the pre-restart checkpoint's resume sequence (verify RG0 byte-repro explicitly as step 1: the log does not print an explicit byte-repro line; confirm whether the check ran in-pipeline or runs in the scorer before adjudication dispatch).
- next steps:
  - After PI restart: RG0 byte-repro verification, then sign-flip mechanism leg (RAM now free), then RR3 adjudication cycle per the printed instructions.
### 037-checkpoint - Checkpoint

- at: `2026-07-14T20:18:57Z`
- kind: `checkpoint`
- summary: RR3 adjudication cycle DISPATCHED. Pool manifest (21 shards, 16045 rows = 14485 core + 474 clear-neg + 1086 clear-pos decoys, seed 20260715) committed to exp/rr3-corrected-placebo as 6204a7f2 BEFORE any grading, per the manifest-before-grading rule. 21 context-free blind graders (sonnet, rubric verbatim from AMENDMENT.md, bare opaque_id+text shards, no experiment context, no pattern-matcher per standing PI directive) spawned in parallel; graded files land in gitignored analysis/graded/.
- next steps:
  - On grader completion: verify line counts/order, apply_adjudication.py commit-hash per shard BEFORE apply, then apply --grading-manifest (CG1 per-shard + pooled, void-regrade-once), then rr3_scorer.py, then red-team BEFORE verdict. signflip-mech agent still running (BG1 mistral/llama real-data checks + M1/M2/M3 mechanism leg).
### 038-checkpoint - Checkpoint

- at: `2026-07-14T20:38:58Z`
- kind: `checkpoint`
- summary: INCIDENT + containment during RR3 blind grading: parallel grader agents shared the session scratchpad for helper scripts and two write collisions occurred on generic filenames (write_shard00.py, verify.py two writers each). Effect: one grader's judgment chunk routed to the wrong target mid-run; the in-flight rider_mistral_shard_01 grader's partial file is missing a ~50-line middle block (720/770, own ids only, no foreign ids). Damage CONTAINED: all 20 completed shards pass full independent integrity (exact counts, positional opaque_id match, no dups within/across files) and every hash commitment was recorded only after that verification; the damaged shard was never hash-committed. PI directive adopted as standing rule: any parallelized agents get pre-assigned PRIVATE working dirs for all intermediates plus unique output paths, forbidden to write elsewhere; zero shared mutable paths. Fold into abstention-grading skill update. Separately: BG1 diagnosis confirmed mistral check-scope defect (0/1694 mismatches on the true evaluated roster; check iterates full 3037-row anchor population, frame_port.py:199-238); llama recompute still running.
- next steps:
  - Await rm01 grader; if final file not cleanly repaired, void attempt (never committed, no unblinding) and dispatch fresh grader with private dir. Then git-commit grading manifest, apply (CG1), rr3_scorer, red-team. Await llama half of BG1 diagnosis, then adjudicate instrument-defect repin vs genuine fail.
### 039-checkpoint - Checkpoint

- at: `2026-07-14T20:56:06Z`
- kind: `checkpoint`
- summary: RR3 RESOLVED FALSIFIED, PR #290 open awaiting PI merge approval. Full adjudication cycle completed: 21/21 shards graded blind and hash-committed pre-unblind (7cec7511), CG1 all-pass per-shard + pooled 0.782, apply clean (14485 rows), scorer: RG1 FAIL effect ratio 1.87 < 3.0 (gated lift +40.9 pts vs fresh random-seed lifts +13.3/-7.4/+21.8 at matched magnitude), RG2/RG3 PASS reproducing RR2. Opus red-team certified artifact-free across all six attack surfaces (directions genuinely random |cos|<=0.015, magnitude-matched, robust detector-only 1.91 and mean-denominator 2.89). Outcome written, resolved falsified, registry regenerated (abaaaf99). Scoreboard adjudicated: PI right llama-null (rider null through 16x, +0.1 at 12x); both wrong on mistral RG1 PASS calls; envelope split (PI inside wrong, orchestrator outside right but 21.8 exceeded his 14-pt bound). KEY METHODOLOGICAL FACT for sign-flip and paper 5: single-seed placebo readings on mistral span -7.4 to +21.8 pts at 12 sigma_c; calibration family-signed placebo map points are single draws; signflip adjudication must read RR3 Outcome first (cross-experiment note in Outcome).
- next steps:
  - 1) PI decision: merge PR #290. 2) signflip: await llama half of bg1-diagnosis (mistral half confirmed check-scope defect, 0/1694 restricted mismatches), then adjudicate repin-vs-drop, then mechanism leg, with RR3 seed-variance caveat folded into any verdict. 3) Paper 5 update for RR3 result after merge. 4) Abstention-grading skill update #42 (+ private-workdir rule).
### 040-checkpoint - Checkpoint

- at: `2026-07-14T22:09:57Z`
- kind: `checkpoint`
- summary: Signflip BG1 adjudicated and closed: both real-data fire-set failures were CHECK-SCOPE defects (lead re-derived mistral 0/1694 restricted personally; llama restricted 1/581 hs20, 0/581 hs22/hs23, known-presence invariant true, read from the diagnostic's raw output log after the diagnostic agent stalled on an unwoken background job). frame_port.py corrected to the actually-gate-evaluated populations (no frame-math change), llama fire-set now gates at 1% tolerance (strictness increase), repinned with full reason, smoke 31 pass, corrected BG1 rerun ALL GREEN (41ae0e37 on exp/placebo-signflip-analysis, after one stale-registry-hook recommit). Mechanism leg (M1/M2/M3 + pre-stated subtype readout) dispatched to harness-builder signflip-mech2. Also this segment: paper 5 updated on main 4bb46ba6 (new 4.9 + seed-variance rule + Section 5 table correction + RR3 AMENDMENT stale-header fix); abstention-grading skill PR #291 MERGED (8bbaa8a1); data-exhaust copy-everything builder + completeness verifier PR #292 OPEN (validated: 4 experiments had zero-file verify-PASSing builds under old allowlist; all 22 slugs rebuild complete, v2 staging in scratch/exhaust-backfill-v2); doubt-snap dry-run card ready, publish awaiting PI go (use v2 build).
- next steps:
  - 1) Review signflip-mech2 M1/M2/M3 + subtype readout, then red-team, then falsifier/scoreboard adjudication + Outcome + resolve + PR (carry RR3 seed-variance caveat). 2) PI: merge PR #292; publish approvals per dataset card (doubt-snap first, from v2). 3) Scaffold placebo seed-distribution census amendment (PI approved as next experiment) after signflip resolves. 4) Then scale test #41.
### 041-checkpoint - Checkpoint

- at: `2026-07-14T22:40:03Z`
- kind: `checkpoint`
- summary: Signflip experiment RESOLVED (PR #293 open, awaiting user merge). Red-team certified all mechanism numbers to full float precision (fire-set 1303/1303; circularity discharged via held-out restriction, -6.05 vs -5.80). M1 axis question resolved from locked instruments: frozen gate defines doubt = -z_d, so doubt axis CONFIRMED all three families under operational convention (near-tautology caveat stated); caution axis not interpretable as question-type ordering; raw-axis prediction_consistent booleans NOT transcribed. Registered falsifier UNTRIGGERED (sign-agnostic, no CI spans 0); behavioral subtype arm FIRES for qwen (future-unknown -24.7 vs <=-2.8; also mistral's +11.8 max and both families' projection outlier). Scoreboard: M1 both correct; subtype PI correct / orchestrator WRONG; M3 both wrong for qwen (null), mistral non-null but 0.3% negligible. M2 carried RR3 single-seed caveat. Stale scaffold header corrected (same bug as RR3). Commit 7904da93, registry regenned, validate OK 72.
- next steps:
  - User decisions pending: merge PR #293 (signflip), merge PR #292 (data-exhaust), doubt-snap publish go (v2 build). Then scaffold placebo seed-distribution census (K=10-20 seeds/family at matched magnitude, approved), then scale test.
