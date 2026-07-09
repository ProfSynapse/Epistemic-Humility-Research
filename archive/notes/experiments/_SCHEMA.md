# Experiment-note schema

An **experiment note** is the agent-runnable instruction manual for one experiment
(and its variations). A collaborator points their agent at a note and the agent
can set it up, run it, document it, and validate it without reconstructing repo
conventions. One note per experiment family; variations live inside the note.

Notes live in `notes/experiments/<slug>.md` and are first-class knowledge-graph
nodes (`kg.id: experiment:<slug>`). They are validated by
`.agents/skills/experiment-runner/scripts/validate_experiment_notes.py` at commit
(`.githooks/pre-commit`) and on every PR (`.github/workflows/validate.yml`).

This file is the contract the validator enforces. Files beginning with `_`
(this file, `_TEMPLATE.md`) are scaffolding, not notes, and are skipped.

## The four layers (do not duplicate across them)

1. Engine = the `experiment-runner` skill (generic how-to-run).
2. Governance = `docs/protocols/phase1/PROTOCOL.md` + `papers/common/amendment-governance.md`.
3. **Experiment note = spec + runbook** (this artifact).
4. Instances = `experiment/phase1/run_records/` + `docs/sessions/`.

A note *references* the protocol and recipes; it does not copy them.

## Required frontmatter

```yaml
---
title: '<human title>'
kg:
  id: experiment:<slug>          # slug must match the filename
  type: experiment
  status: canonical
tags:
  - kg/experiment                # required by the typed KG validator
status: proposed                 # proposed | ready | running | blocked | done | superseded
governance: exploratory          # exploratory | amendment | locked
phase: phase3                    # phase1 | phase2 | phase3 | phase4 | ...
lane: local                      # local | cloud | either
est_compute: '<one line>'        # e.g. "~6 GPU-hours on one RTX 3090"
relationships:                   # typed KG edges from edge-ontology.yaml; MUST include >=1 `tests` edge
  - type: tests
    target: '[[gap-4-probe-transfer]]'
    target_id: gap:4-probe-transfer
    confidence: high
  - type: builds_on
    target: '[[2606.24790--grad-detect-gradient-hallucination-detection]]'
    target_id: paper:2606.24790
related:                         # projection of every edge target
  - '[[gap-4-probe-transfer]]'
---
```

Enum values are fixed; the validator rejects anything else. `status` tracks the
experiment lifecycle; `governance` gates what an agent may change (below).
Every experiment note is a KG node and must carry `tags: [kg/experiment]`.

Relationship types are ontology-governed. Do not invent local edge names such as
`governed_by`; choose an existing edge from
`.skills/knowledge-graph/references/edge-ontology.yaml`, or keep the reference
in prose when no valid typed edge exists. `related` must project every
relationship target.

## Required body sections (`##` headings, in any order)

- **Question & Hypothesis** : RQ, hypothesis, falsifier. For `locked`/`amendment`
  notes, cite the `PROTOCOL.md` section instead of restating pre-registered claims.
- **Design** : arms/conditions, pinned models, datasets, metric panel, seeds /
  sample size / power. `exploratory` notes must carry this inline.
- **Prerequisites & Gating** : what must exist or pass before a run (data present,
  checkpoints, GPU, leakage guard). Name the gating commands.
- **Runbook** : ordered steps an agent follows (setup -> run -> eval -> document),
  each pointing at a script/recipe by path. See "Runbook path rule" below.
- **Validation contract** : pre-run assertions (counts), post-run checks (artifacts
  exist + schema-valid), and an explicit definition of done.
- **Outputs & provenance** : where run records / eval / session notes land, and how
  results feed (or do not feed) the meta-analysis.
- **Variations** : the sweep and how each variant differs.
- **Status log** : dated lines + links to instances run so far.

## Governance rule

- `locked` / `amendment` : the note must reference `PROTOCOL.md` (a section). An
  agent must NOT change the design without the `amendment-governance.md` 7-point
  sign-off. The validator requires the word `PROTOCOL` to appear.
- `exploratory` : freely editable; results are non-headline. The validator
  requires a non-empty Design section.

## Runbook path rule

Any backticked token in the **Runbook** section that looks like a repo path
(starts with one of `experiment/ experiments/ library/ meta-analysis/ bin/ tools/ docs/
notes/ papers/ archive/ .agents/ .skills/ .claude/ .github/`) must exist on disk. This catches rot when a
referenced script or recipe is renamed or removed. Commands, flags, and external
paths are ignored. Keep brittle inline commands out; point at checked-in scripts.

## Index

`notes/experiments/README.md` is the auto-generated registry (status | phase | gap
| lane). Regenerate it with:

```bash
python3 .agents/skills/experiment-runner/scripts/validate_experiment_notes.py notes/experiments --emit-index
```

Before committing new or edited notes, also run the KG relationship validator:

```bash
python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py library notes/experiments
python3 bin/validate_kg.py
```
