---
schema_version: research-session/v1
session_id: 20260708T171528Z-experiment-provenance-cleanup-architecture
title: Experiment Provenance Cleanup Architecture
status: active
created_at: '2026-07-08T17:15:28Z'
updated_at: '2026-07-08T18:09:29Z'
track: research
question: How should old protocol amendments, new experiments-first records, and research
  session notes be aligned for multiplayer research without breaking provenance?
tags:
- experiment-runner
- provenance
- infrastructure
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-planning
  at: '2026-07-08T17:16:48Z'
  kind: planning
  title: Provenance cleanup proposal drafted
  summary: Created a draft architecture proposal for aligning legacy protocol amendments,
    experiments-first records, and session-note naming around semantic IDs, generated
    registries, and collision-resistant future filenames without mass-renaming historical
    provenance.
  evidence:
  - docs/architecture/experiment-provenance-cleanup.md
  run_ids: []
  commands: []
  decisions:
  - Use stable semantic IDs for identity, generated registries for order, and timestamped
    filenames for future session notes; treat mass renames of legacy governed docs
    as out of scope unless a specific reference is broken.
  next_steps: []
  signals: {}
- id: 002-infrastructure
  at: '2026-07-08T17:20:48Z'
  kind: infrastructure
  title: Session and experiment scaffold helpers hardened
  summary: Updated the canonical experiment-runner and experiments skills so new session
    notes default to timestamped collision-resistant filenames, session validation
    enforces unique session_id values, and new experiment manifests receive created_at
    at scaffold time. Synced generated skill mirrors and verified narrow tests.
  evidence:
  - .skills/experiment-runner/scripts/research_session.py
  - .skills/experiments/scripts/exp.py
  - docs/architecture/experiment-provenance-cleanup.md
  run_ids: []
  commands:
  - python3 -m pytest .skills/experiment-runner/tests/test_run_matrix.py .skills/experiments/tests/test_exp.py
    -q
  - python3 .agents/skills/experiment-runner/scripts/research_session.py validate
    docs/sessions
  - bin/exp validate
  decisions:
  - 'Keep the existing scaffold commands as the public interface: research_session.py
    init for session notes and bin/exp new for experiments; improve their defaults
    instead of adding parallel one-off generators.'
  next_steps: []
  signals: {}
- id: 003-validation
  at: '2026-07-08T17:34:20Z'
  kind: validation
  title: Provenance audit includes library references
  summary: 'Added a read-only provenance audit that scans repo reference files, including
    library, before migration. Current audit surface: 40 legacy amendment files, 11
    experiments-first manifests, 115 files with experiment/amendment links, including
    14 under library; duplicate session IDs are now zero but legacy numbered filenames
    and serial-only IDs remain migration debt.'
  evidence:
  - .skills/experiment-runner/scripts/provenance_audit.py
  - docs/architecture/experiment-provenance-cleanup.md
  run_ids: []
  commands:
  - python3 .agents/skills/experiment-runner/scripts/provenance_audit.py
  decisions:
  - 'Full migration is the desired end-state: legacy amendments are migration inputs
    to move into experiments/<slug>/, and path rewrites must cover docs, experiment,
    experiments, library, and skill/reference files.'
  next_steps: []
  signals: {}
- id: 004-result
  at: '2026-07-08T17:45:44Z'
  kind: result
  title: Legacy amendments migrated into experiments layout
  summary: Migrated all 40 legacy experiment/protocol/AMENDMENT-*.md records into
    experiments/<slug>/ as historical-amendment/historical records, generated docs/migration/experiment-path-map.json,
    rewrote active references across docs, experiment, experiments, library, skills,
    and scripts, regenerated experiments registry, and verified the audit now reports
    51 experiments-first manifests, 0 legacy amendment files, and 0 active legacy
    amendment link targets. Remaining legacy path strings are compatibility metadata
    or byte-pinned AP instrument provenance.
  evidence:
  - docs/migration/experiment-path-map.json
  - experiments/REGISTRY.md
  - docs/architecture/experiment-provenance-cleanup.md
  run_ids: []
  commands:
  - python3 .agents/skills/experiments/scripts/migrate_legacy_amendments.py --apply
  - python3 .agents/skills/experiment-runner/scripts/provenance_audit.py
  - bin/exp validate && bin/exp regen --check
  - python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py library
    notes/experiments && python3 bin/validate_kg.py
  decisions:
  - Use historical-amendment/historical for imported legacy records and leave falsifier/type/instrument/kg
    manual-review fields explicit until each migrated AMENDMENT.md is hand-read.
  next_steps: []
  signals: {}
- id: 005-result
  at: '2026-07-08T17:58:14Z'
  kind: result
  title: Session filenames migrated and live old-path instructions retired
  summary: Migrated 49 legacy numbered session-note filenames into timestamped stems,
    preserving old IDs under legacy_session while updating live references from the
    session path map. Fixed the migration tool so legacy_session.path is restored
    without reverting body references. Updated backlog, README, project instructions,
    prediction-scoreboard query, library provenance notes, and AP instrument comments
    to point at experiments-first records. AP pins were refreshed after comment-only
    path updates. Verification now reports 50 session files, 0 legacy numbered
    filenames, 0 duplicate session IDs, 0 active shorthand session refs, 51 experiment
    manifests, 0 legacy amendment files, and 0 active legacy amendment link targets.
  evidence:
  - docs/migration/session-path-map.json
  - .skills/experiment-runner/scripts/migrate_sessions.py
  - bin/build_backlog_index.py
  - docs/architecture/experiment-provenance-cleanup.md
  run_ids: []
  commands:
  - python3 .agents/skills/experiment-runner/scripts/migrate_sessions.py --apply
  - python3 .agents/skills/experiment-runner/scripts/research_session.py validate
    docs/sessions
  - python3 .agents/skills/experiment-runner/scripts/provenance_audit.py
  - python3 bin/build_backlog_index.py --write
  - bin/exp validate && bin/exp regen
  decisions:
  - Preserve old session paths only as compatibility provenance in legacy_session.path
    and docs/migration/session-path-map.json; active references should use timestamped
    session paths.
  next_steps: []
  signals: {}
- id: 006-result
  at: '2026-07-08T18:09:29Z'
  kind: result
  title: Papers, experiment notes, and archive separated
  summary: Moved active paper production out of experiment/paper into top-level
    papers/<paper>/ directories with local manuscript, analysis, figures, scripts,
    and notes surfaces. Moved superseded paper drafts and the retired provenance
    inventory into visible archive/papers/ rather than a hidden dot-directory. Moved
    reusable experiment-family runbook notes from experiment/notes/ to
    notes/experiments/. Added paper and notes migration maps, updated CI/pre-commit,
    KG schema docs, skill docs, README, AGENTS/CLAUDE, and figure builders to the
    new homes.
  evidence:
  - papers/README.md
  - notes/README.md
  - archive/README.md
  - docs/migration/paper-path-map.json
  - docs/migration/notes-path-map.json
  run_ids: []
  commands: []
  decisions:
  - Use visible archive/ instead of .archive because archived provenance must stay
    discoverable to agents and reviewers; dot-directories remain tool-state/mirror
    territory by default.
  next_steps: []
  signals: {}
---
# Experiment Provenance Cleanup Architecture

## Question

How should old protocol amendments, new experiments-first records, and research session notes be aligned for multiplayer research without breaking provenance?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-planning - Provenance cleanup proposal drafted

- at: `2026-07-08T17:16:48Z`
- kind: `planning`
- summary: Created a draft architecture proposal for aligning legacy protocol amendments, experiments-first records, and session-note naming around semantic IDs, generated registries, and collision-resistant future filenames without mass-renaming historical provenance.
- evidence:
  - `docs/architecture/experiment-provenance-cleanup.md`
- decisions:
  - Use stable semantic IDs for identity, generated registries for order, and timestamped filenames for future session notes; treat mass renames of legacy governed docs as out of scope unless a specific reference is broken.
### 002-infrastructure - Session and experiment scaffold helpers hardened

- at: `2026-07-08T17:20:48Z`
- kind: `infrastructure`
- summary: Updated the canonical experiment-runner and experiments skills so new session notes default to timestamped collision-resistant filenames, session validation enforces unique session_id values, and new experiment manifests receive created_at at scaffold time. Synced generated skill mirrors and verified narrow tests.
- evidence:
  - `.skills/experiment-runner/scripts/research_session.py`
  - `.skills/experiments/scripts/exp.py`
  - `docs/architecture/experiment-provenance-cleanup.md`
- commands:
  - `python3 -m pytest .skills/experiment-runner/tests/test_run_matrix.py .skills/experiments/tests/test_exp.py -q`
  - `python3 .agents/skills/experiment-runner/scripts/research_session.py validate docs/sessions`
  - `bin/exp validate`
- decisions:
  - Keep the existing scaffold commands as the public interface: research_session.py init for session notes and bin/exp new for experiments; improve their defaults instead of adding parallel one-off generators.
### 003-validation - Provenance audit includes library references

- at: `2026-07-08T17:34:20Z`
- kind: `validation`
- summary: Added a read-only provenance audit that scans repo reference files, including library, before migration. Current audit surface: 40 legacy amendment files, 11 experiments-first manifests, 115 files with experiment/amendment links, including 14 under library; duplicate session IDs are now zero but legacy numbered filenames and serial-only IDs remain migration debt.
- evidence:
  - `.skills/experiment-runner/scripts/provenance_audit.py`
  - `docs/architecture/experiment-provenance-cleanup.md`
- commands:
  - `python3 .agents/skills/experiment-runner/scripts/provenance_audit.py`
- decisions:
  - Full migration is the desired end-state: legacy amendments are migration inputs to move into experiments/<slug>/, and path rewrites must cover docs, experiment, experiments, library, and skill/reference files.
### 004-result - Legacy amendments migrated into experiments layout

- at: `2026-07-08T17:45:44Z`
- kind: `result`
- summary: Migrated all 40 legacy experiment/protocol/AMENDMENT-*.md records into experiments/<slug>/ as historical-amendment/historical records, generated docs/migration/experiment-path-map.json, rewrote active references across docs, experiment, experiments, library, skills, and scripts, regenerated experiments registry, and verified the audit now reports 51 experiments-first manifests, 0 legacy amendment files, and 0 active legacy amendment link targets. Remaining legacy path strings are compatibility metadata or byte-pinned AP instrument provenance.
- evidence:
  - `docs/migration/experiment-path-map.json`
  - `experiments/REGISTRY.md`
  - `docs/architecture/experiment-provenance-cleanup.md`
- commands:
  - `python3 .agents/skills/experiments/scripts/migrate_legacy_amendments.py --apply`
  - `python3 .agents/skills/experiment-runner/scripts/provenance_audit.py`
  - `bin/exp validate && bin/exp regen --check`
  - `python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py library notes/experiments && python3 bin/validate_kg.py`
- decisions:
  - Use historical-amendment/historical for imported legacy records and leave falsifier/type/instrument/kg manual-review fields explicit until each migrated AMENDMENT.md is hand-read.
### 005-result - Session filenames migrated and live old-path instructions retired

- at: `2026-07-08T17:58:14Z`
- kind: `result`
- summary: Migrated 49 legacy numbered session-note filenames into timestamped stems, preserving old IDs under `legacy_session` while updating live references from the session path map. Fixed the migration tool so `legacy_session.path` is restored without reverting body references. Updated backlog, README, project instructions, prediction-scoreboard query, library provenance notes, and AP instrument comments to point at experiments-first records. AP pins were refreshed after comment-only path updates. Verification now reports 50 session files, 0 legacy numbered filenames, 0 duplicate session IDs, 0 active shorthand session refs, 51 experiment manifests, 0 legacy amendment files, and 0 active legacy amendment link targets.
- evidence:
  - `docs/migration/session-path-map.json`
  - `.skills/experiment-runner/scripts/migrate_sessions.py`
  - `bin/build_backlog_index.py`
  - `docs/architecture/experiment-provenance-cleanup.md`
- commands:
  - `python3 .agents/skills/experiment-runner/scripts/migrate_sessions.py --apply`
  - `python3 .agents/skills/experiment-runner/scripts/research_session.py validate docs/sessions`
  - `python3 .agents/skills/experiment-runner/scripts/provenance_audit.py`
  - `python3 bin/build_backlog_index.py --write`
  - `bin/exp validate && bin/exp regen`
- decisions:
  - Preserve old session paths only as compatibility provenance in `legacy_session.path` and `docs/migration/session-path-map.json`; active references should use timestamped session paths.
### 006-result - Papers, experiment notes, and archive separated

- at: `2026-07-08T18:09:29Z`
- kind: `result`
- summary: Moved active paper production out of `experiment/paper` into top-level `papers/<paper>/` directories with local manuscript, analysis, figures, scripts, and notes surfaces. Moved superseded paper drafts and the retired provenance inventory into visible `archive/papers/` rather than a hidden dot-directory. Moved reusable experiment-family runbook notes from `experiment/notes/` to `notes/experiments/`. Added paper and notes migration maps, updated CI/pre-commit, KG schema docs, skill docs, README, AGENTS/CLAUDE, and figure builders to the new homes.
- evidence:
  - `papers/README.md`
  - `notes/README.md`
  - `archive/README.md`
  - `docs/migration/paper-path-map.json`
  - `docs/migration/notes-path-map.json`
- decisions:
  - Use visible `archive/` instead of `.archive` because archived provenance must stay discoverable to agents and reviewers; dot-directories remain tool-state/mirror territory by default.
