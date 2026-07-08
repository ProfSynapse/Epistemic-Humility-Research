# Experiment Notes

Use this reference when creating or editing files under `notes/experiments/`.
Experiment notes are runnable research specs, not scratch notes: they should let
a future agent set up, run, validate, and document one experiment family without
reconstructing project conventions from memory.

## Required context

Read these before editing:

- `notes/experiments/_SCHEMA.md`
- `notes/experiments/_TEMPLATE.md` when creating a new note
- `.skills/knowledge-graph/references/edge-ontology.yaml` when choosing KG edges

## Authoring rules

- Include `tags: [kg/experiment]`; experiment notes are KG nodes.
- Keep `kg.id` as `experiment:<filename-stem>`.
- Include at least one `relationships` edge with `type: tests`.
- Use only ontology-defined relationship types. Do not invent edges such as
  `governed_by`; cite protocols or amendments in prose unless an existing edge
  cleanly represents the relationship.
- Project every relationship target into `related`.
- Keep runbook steps pointed at checked-in scripts, recipes, or docs. The
  validator checks backticked repo paths in the Runbook section for rot.
- For `amendment` or `locked` governance, cite `PROTOCOL.md` and follow
  `reference/protocol-amendments.md` before changing design.

## Validation sequence

Run these before committing:

```bash
python3 .agents/skills/experiment-runner/scripts/validate_experiment_notes.py notes/experiments
python3 .agents/skills/experiment-runner/scripts/validate_experiment_notes.py notes/experiments --emit-index
python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py library notes/experiments
python3 bin/validate_kg.py
```

Files beginning with `_` are scaffolding and are skipped by the experiment-note
and KG relationship validators. Real experiment notes should be warning-clean
where practical and error-clean always.
