---
schema_version: research-session/v1
session_id: 20260708T164625Z-paper-5-j-space-hardening
title: Paper 5 J-space hardening
status: active
created_at: '2026-07-08T16:46:25Z'
updated_at: '2026-07-08T17:58:00Z'
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
checkpoints: []
legacy_session:
  id: paper5-jspace-hardening
  path: docs/sessions/0044 - paper-5-j-space-hardening.md
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
