# Experiment Runbooks And Plans

Use this reference when creating or editing experiment-local `RUNBOOK.md` and
`PLAN.md` files under `experiments/<slug>/`. These files are runnable research
specs, not scratch notes: they should let a future agent set up, run, validate,
and document one experiment without reconstructing project conventions from
memory.

## Required context

Read these before editing:

- `experiments/<slug>/AMENDMENT.md`
- `experiments/<slug>/experiment.yaml`
- `.skills/knowledge-graph/references/edge-ontology.yaml` when choosing KG edges

## Authoring rules

- Keep `RUNBOOK.md` operational: setup, gates, commands, validation, outputs,
  and provenance links.
- Keep `PLAN.md` prospective: scope, prerequisites, dependencies, launch
  decision points, and what must become true before it is runnable.
- Do not duplicate governed outcomes from `AMENDMENT.md`; link to the source of
  truth instead.
- Keep runbook steps pointed at checked-in scripts, recipes, or docs. The
  experiment validator checks manifests and the KG validator checks library
  concept notes; stale command/path checks should be added as focused tests when
  a runbook becomes operationally critical.
- For `amendment` or `locked` governance, cite `PROTOCOL.md` and follow
  `reference/protocol-amendments.md` before changing design.

## Validation sequence

Run these before committing:

```bash
bin/exp validate
bin/exp regen --check
python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py library
python3 bin/validate_kg.py
```

Legacy top-level experiment notes were retired to `archive/notes/experiments/`.
Do not create new active notes under `notes/experiments/`.
