---
schema_version: research-session/v1
session_id: paper5-jspace-hardening
title: Paper 5 J-space hardening
status: active
created_at: '2026-07-08T16:46:25Z'
updated_at: '2026-07-09T19:21:21Z'
phase: phase1
question: Which registered follow-up experiments harden the Paper 5 actuation thesis,
  starting with a fresh Qwen3-4B J-space layer-site replication?
tags:
- paper5
- j-space
- actuation
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Paper 5 draft merged to main; same-model J-space layer-site replication
    being registered before cross-family escalation.
  changed_by_session: Created the fresh-pool replication amendment scaffold and row-mining/extraction/contrast
    instrument.
checkpoints:
- id: 001-decision
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
- id: 002-result
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
- id: 003-interpretation
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
  - `experiment/paper/paper5-actuation-draft-v0.md`
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
  - `/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl`
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
### 001-decision - Decision

- at: `2026-07-09T13:54:25Z`
- kind: `decision`
- summary: Replication signed and launched; cross-family queued with dedup constraint. User prediction recorded (full replication, +18-25pp) alongside orchestrator (holds-but-shrinks, +10-18pp); j-space-layer-contrast-replication signed (826d9a1c on agent/jspace-full-run) and the full 4-layer contrast launched on the local 3090. Scaffolded j-space-cross-family-layer-contrast (d2134050 on exp/j-space-cross-family-layer-contrast) using Amendment Z's family panel. Worktree audit found the signed doubt-snap-cross-family-confirmatory mid-run on Modal over an overlapping panel: to avoid duplicating its per-family FIT pipeline, the cross-family layer contrast HOLDS unsigned until that run resolves and is revised to consume its pools/splits/late-site artifacts. Also inherited its pre-outcome loader finding by substituting Mistral-7B-Instruct-v0.3 for Amendment Z's Ministral-3-3B (Mistral3ForConditionalGeneration is not a causal-LM write substrate). Open decision points for sign time: G3 late-reference floor 0.40/0.30 is a draft guess; multimodal loader paths and per-family EOS lists unverified.
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md`
  - `/home/profsynapse/code/ehr-worktrees/jspace-cross-family/experiments/j-space-cross-family-layer-contrast/AMENDMENT.md`
  - `/home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md`
### 002-result - Result

- at: `2026-07-09T17:28:55Z`
- kind: `result`
- summary: Replication resolved: registered G1 FAIL (null-result), PR #263. Full run completed flawlessly on the 3090 (exact readback, zero collapse, all 2,263 rows x 4 arms). Best mid-band hs29 99.67% vs hs34 94.12% = +5.6pp, under the 10pp bar; G2/G3 passed; both scoreboard predictions wrong. Post-run red-team reproduced every number and corrected the mechanism story before the Outcome was written: ceiling effect with a structural cause (fresh confabs single-source kuq_ku_unknown_x, the two harder predecessor sources absent from the candidate universe), so this is a narrower-distribution replication; direction survives with CI separation at hs23/hs29 (not hs26); hs34 deficit is write-effectiveness not gate-transfer; hs29 has the worst known-correct cost. Carried forward: Paper 5 pool-sensitivity caveat; cross-family experiment needs a ceiling-robust G1 (CI separation + failure-ratio) and multi-source confab mining before sign. Infra shipped same session: tuner RunLog (Synaptic-Tuner PR #141) + consumption/skill invariant (PR #262) after catching the buffered-run risk mid-flight; per-row persistence gap in this run is the motivating case.
- evidence:
  - `experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md`
  - `https://github.com/ProfSynapse/Epistemic-Humility-Research/pull/263`
### 003-interpretation - Interpretation

- at: `2026-07-09T19:21:21Z`
- kind: `interpretation`
- summary: Qwen3.5 doubt-snap dose-fit failure audited: overdose collapse, NOT a family null and NOT an inert write. Opus audit of the Modal artifacts falsified the hook-path/inert-write hypothesis (readback write_ok=true, commanded ~100 realized 99.96-100.04, layer 29 correctly derived from nested text_config) and the grader/render hypothesis (baseline well-formed 0.995/0.987). Root cause for BOTH cells: the registered absolute dose grid {100,150,200,250} is mis-scaled to Qwen3.5 residual geometry. Qwen3.5-4B sigma_c=2.80 (4.7x smaller than the working Qwen3-4B reference) puts even dose 100 at 38-sigma: 854/854 fired confabs degenerate (repeating I-dont-know token to cap). Qwen3.5-9B shows textbook dose-graded collapse: refused 18->363->886 across 100->150->200 while well_formed falls 886->503->2 (JSON colon corrupts before content); peak clean 5.1% at dose 150; its coherent window sits below/between the grid. Key science: sigma-distance is NOT portable across models (9B at 15.8 sigma matched the reference's working point and still collapsed); usable windows are absolute and model-specific, consistent with the J-space dose-calibration prior. Disposition: instrument failure, NOT-RUN candidates, must not be reported as doubt-snap-null-on-Qwen3.5 (9B refuses 97% of confabs on command). Honest limit: no proof a window clearing 60%/10% exists; grid never sampled below 100. Gap found: Modal rows carry no per-row readback field (smoke-only), unlike the local pipeline. Proposed (NOT run): finer low grids (4B ~10-75, 9B ~60-140) reusing volume artifacts, ~1-2 GPU-h ~$1-3/cell, but this changes the LOCKED grid and needs a signed revision -- lifted to user.
- evidence:
  - `/home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/analysis/from_modal/qwen35_4b/committed/dose_fit.json`
  - `/home/profsynapse/code/ehr-worktrees/doubt-snap-cross-family/experiments/doubt-snap-cross-family-confirmatory/analysis/from_modal/qwen35_9b/committed/build_manifest.json`
