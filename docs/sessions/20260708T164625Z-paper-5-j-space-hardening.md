---
schema_version: research-session/v1
session_id: 20260708T164625Z-paper-5-j-space-hardening
title: Paper 5 J-space hardening
status: active
created_at: '2026-07-08T16:46:25Z'
updated_at: '2026-07-13T02:53:31Z'
track: research
phase: phase1
question: Which registered follow-up experiments harden the Paper 5 actuation thesis,
  starting with a fresh Qwen3-4B J-space layer-site replication?
tags:
- paper5
- j-space
- actuation
run_ids: []
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
