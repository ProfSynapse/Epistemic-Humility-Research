---
schema_version: research-session/v1
session_id: 20260708T164625Z-paper-5-j-space-hardening
title: Paper 5 J-space hardening
status: active
created_at: '2026-07-08T16:46:25Z'
updated_at: '2026-07-10T19:19:39Z'
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
