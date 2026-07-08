---
schema_version: research-session/v1
session_id: 20260624T111205Z-grad-detect-ingest-kg-ingest-skill-rework-exploratory-gradient-probe-map
title: Grad Detect ingest, kg-ingest skill rework, exploratory gradient-probe map
status: active
created_at: '2026-06-24T11:12:05Z'
updated_at: '2026-06-24T11:41:59Z'
phase: phase3
question: Ingest Grad Detect (2606.24790) into the KG, fix the kg-ingest skill's friction,
  place it in the meta-analysis, and map exploratory experiments.
tags:
- kg-ingest
- gradient-probe
- gap4
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-infrastructure
  at: '2026-06-24T11:12:52Z'
  kind: infrastructure
  title: Grad Detect ingested into the knowledge graph
  summary: 'Folded 2606.24790 into the library KG by hand: 4 new atoms (method:grad-detect,
    dataset:popqa, 2 mechanisms), reusing existing benchmark/metric/term atoms; patched
    the paper note with typed edges + Claims + Summary/Extracted-numbers/Relevance.
    Validates clean (241 notes, 0 unresolved, 0 orphans); paper is a degree-18 node.'
  evidence:
  - library/notes/2606.24790--grad-detect-gradient-hallucination-detection.md
  - library/concepts/methods/grad-detect.md
  run_ids: []
  commands: []
  decisions:
  - Did the single paper by hand rather than via the batch Workflow.
  next_steps: []
  signals: {}
- id: 002-infrastructure
  at: '2026-06-24T11:12:52Z'
  kind: infrastructure
  title: kg-ingest skill reworked + paper-fetch tooling added
  summary: Restructured SKILL.md around the real five-move shape with single-paper-by-hand
    as default; added inline authoring templates, manual finalize one-liner, and the
    search-reindex step. New fetch_paper.py (arXiv API metadata + curl HTML/PDF download
    + note stub + NEW/STUB/INGESTED --check, idempotent, no dup notes) and scan_entities.py.
    Promoted kg-ingest into canonical .skills/ under sync governance.
  evidence:
  - .skills/kg-ingest/SKILL.md
  - .skills/kg-ingest/scripts/fetch_paper.py
  run_ids: []
  commands: []
  decisions:
  - fetch_paper.py shells out to curl to dodge macOS Python SSL cert failure; existence
    detection by arXiv id glob, not slug, so re-runs never duplicate a note.
  next_steps: []
  signals: {}
- id: 003-decision
  at: '2026-06-24T11:12:52Z'
  kind: decision
  title: 'Meta-analysis placement: methods-narrative + v1 candidate, not effects.csv'
  summary: Grad Detect is a detector, not a training-intervention effect, so it stays
    out of the pooled effects.csv. Logged as a post-synthesis v1 candidate in prisma-flow.md,
    relevant to draft section 6.3 Gap 4 (probe modality) and 8.3 Phase 3; frozen review
    body untouched.
  evidence:
  - meta-analysis/evidence/prisma-flow.md
  run_ids: []
  commands: []
  decisions:
  - User chose methods-narrative + citation-gap; keep effects.csv sign-tests clean.
  next_steps: []
  signals: {}
- id: 004-planning
  at: '2026-06-24T11:12:52Z'
  kind: planning
  title: Exploratory gradient-probe experiment map (E1-E4)
  summary: 'Mapped four exploratory arms framing a gradient probe as a candidate L-gradient
    layer in the coherent-humility stack: E1 modality bake-off, E2 truth-vs-recall
    via PopQA popularity, E3 probe-transfer across SFT/DPO/KTO (Gap 4 / Phase 3, gated
    on checkpoints), E4 layer-localization byproduct. Exploratory: not a v0.3 amendment,
    no runs.'
  evidence:
  - experiment/protocol/EXPLORATORY-gradient-probes.md
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Pick base model (Qwen2.5-1.5B vs Gemma-2-2B) and lift the exact gradient-feature
    recipe from the paper appendix before building E1.
  - E3 waits on Phase-1 SFT/DPO/KTO checkpoints.
  signals: {}
- id: 005-infrastructure
  at: '2026-06-24T11:41:59Z'
  kind: infrastructure
  title: Experiment-note infrastructure (pass 1) built + validated
  summary: 'Built the experiment-note system: notes/experiments/_SCHEMA.md + _TEMPLATE.md
    contract; typed experiment + gap KG node types and tests/builds_on edges (edge-ontology.yaml
    synced across all 3 skill mirrors; convert.py + library/SCHEMA.md updated); gap:4-probe-transfer
    node; validate_experiment_notes.py (canonical in experiment-runner, synced) with
    bin/validate-experiments{,.py,.cmd} wrappers checking frontmatter enums, required
    sections, governance rule, runbook-path existence, and a tests edge, plus --emit-index
    for notes/experiments/README.md. Wired into BOTH gates: .githooks/pre-commit and
    new .github/workflows/validate.yml CI for PR auto-reject. First real note gradient-probe-coherence.md
    migrated from EXPLORATORY-gradient-probes.md (now a pointer). Verified end-to-end:
    sync --check in sync; validate_kg exit 0; kg relationships 0 errors; emit-index
    OK; reindex surfaces the experiment + gap nodes; NEGATIVE tests confirm the validator
    AND the pre-commit hook reject a malformed note (missing sections / bad enum /
    bad runbook path) with clear messages, exit 1, and pass clean after removal.'
  evidence: []
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
legacy_session:
  id: grad-detect-ingest-and-exploratory
  path: docs/sessions/0009 - grad-detect-ingest-kg-ingest-skill-rework-exploratory-gradient-probe-map.md
---
# Grad Detect ingest, kg-ingest skill rework, exploratory gradient-probe map

## Question

Ingest Grad Detect (2606.24790) into the KG, fix the kg-ingest skill's friction, place it in the meta-analysis, and map exploratory experiments.

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-infrastructure - Grad Detect ingested into the knowledge graph

- at: `2026-06-24T11:12:52Z`
- kind: `infrastructure`
- summary: Folded 2606.24790 into the library KG by hand: 4 new atoms (method:grad-detect, dataset:popqa, 2 mechanisms), reusing existing benchmark/metric/term atoms; patched the paper note with typed edges + Claims + Summary/Extracted-numbers/Relevance. Validates clean (241 notes, 0 unresolved, 0 orphans); paper is a degree-18 node.
- evidence:
  - `library/notes/2606.24790--grad-detect-gradient-hallucination-detection.md`
  - `library/concepts/methods/grad-detect.md`
- decisions:
  - Did the single paper by hand rather than via the batch Workflow.
### 002-infrastructure - kg-ingest skill reworked + paper-fetch tooling added

- at: `2026-06-24T11:12:52Z`
- kind: `infrastructure`
- summary: Restructured SKILL.md around the real five-move shape with single-paper-by-hand as default; added inline authoring templates, manual finalize one-liner, and the search-reindex step. New fetch_paper.py (arXiv API metadata + curl HTML/PDF download + note stub + NEW/STUB/INGESTED --check, idempotent, no dup notes) and scan_entities.py. Promoted kg-ingest into canonical .skills/ under sync governance.
- evidence:
  - `.skills/kg-ingest/SKILL.md`
  - `.skills/kg-ingest/scripts/fetch_paper.py`
- decisions:
  - fetch_paper.py shells out to curl to dodge macOS Python SSL cert failure; existence detection by arXiv id glob, not slug, so re-runs never duplicate a note.
### 003-decision - Meta-analysis placement: methods-narrative + v1 candidate, not effects.csv

- at: `2026-06-24T11:12:52Z`
- kind: `decision`
- summary: Grad Detect is a detector, not a training-intervention effect, so it stays out of the pooled effects.csv. Logged as a post-synthesis v1 candidate in prisma-flow.md, relevant to draft section 6.3 Gap 4 (probe modality) and 8.3 Phase 3; frozen review body untouched.
- evidence:
  - `meta-analysis/evidence/prisma-flow.md`
- decisions:
  - User chose methods-narrative + citation-gap; keep effects.csv sign-tests clean.
### 004-planning - Exploratory gradient-probe experiment map (E1-E4)

- at: `2026-06-24T11:12:52Z`
- kind: `planning`
- summary: Mapped four exploratory arms framing a gradient probe as a candidate L-gradient layer in the coherent-humility stack: E1 modality bake-off, E2 truth-vs-recall via PopQA popularity, E3 probe-transfer across SFT/DPO/KTO (Gap 4 / Phase 3, gated on checkpoints), E4 layer-localization byproduct. Exploratory: not a v0.3 amendment, no runs.
- evidence:
  - `experiment/protocol/EXPLORATORY-gradient-probes.md`
- next steps:
  - Pick base model (Qwen2.5-1.5B vs Gemma-2-2B) and lift the exact gradient-feature recipe from the paper appendix before building E1.
  - E3 waits on Phase-1 SFT/DPO/KTO checkpoints.
### 005-infrastructure - Experiment-note infrastructure (pass 1) built + validated

- at: `2026-06-24T11:41:59Z`
- kind: `infrastructure`
- summary: Built the experiment-note system: notes/experiments/_SCHEMA.md + _TEMPLATE.md contract; typed experiment + gap KG node types and tests/builds_on edges (edge-ontology.yaml synced across all 3 skill mirrors; convert.py + library/SCHEMA.md updated); gap:4-probe-transfer node; validate_experiment_notes.py (canonical in experiment-runner, synced) with bin/validate-experiments{,.py,.cmd} wrappers checking frontmatter enums, required sections, governance rule, runbook-path existence, and a tests edge, plus --emit-index for notes/experiments/README.md. Wired into BOTH gates: .githooks/pre-commit and new .github/workflows/validate.yml CI for PR auto-reject. First real note gradient-probe-coherence.md migrated from EXPLORATORY-gradient-probes.md (now a pointer). Verified end-to-end: sync --check in sync; validate_kg exit 0; kg relationships 0 errors; emit-index OK; reindex surfaces the experiment + gap nodes; NEGATIVE tests confirm the validator AND the pre-commit hook reject a malformed note (missing sections / bad enum / bad runbook path) with clear messages, exit 1, and pass clean after removal.
