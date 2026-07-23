---
name: knowledge-graph
description: Create, validate, normalize, export, and analyze typed Obsidian knowledge graph metadata in the Professor Synapse vault, including `kg` node metadata, `relationships` edge objects, `related` link projections, ontology-governed edge types, legacy relationship shorthand, and graph analysis reports.
---

# Knowledge Graph

## Overview

Use this skill when working with typed knowledge graph metadata in Obsidian notes. Keep Obsidian useful for linking and browsing while making the graph deterministic enough to validate, export, and analyze with scripts.

## Canonical Shape

Use `kg` for node metadata, `relationships` for typed directed edges, and `related` for the Obsidian-native projection of edge targets.

```yaml
---
title: "Benzion Netanyahu"
aliases:
  - Benzion Mileikowsky
tags:
  - kg/person
kg:
  id: person:benzion-netanyahu
  type: person
  status: canonical
related:
  - "[[Benjamin Netanyahu]]"
  - "[[Cornell University]]"
relationships:
  - type: father_of
    target: "[[Benjamin Netanyahu]]"
    target_id: person:benjamin-netanyahu
    confidence: high
  - type: taught_at
    target: "[[Cornell University]]"
    target_id: org:cornell-university
    confidence: medium
---
```

Rules:

- Treat the current note as the source node for every relationship.
- Use one relationship object per directed edge.
- Make `type` a canonical ontology edge in `snake_case`.
- Make `target` an Obsidian wikilink string, quoted in YAML.
- Add every relationship target to `related` so native Obsidian links, Graph view, and Bases can see the note-to-note connection.
- Use `kg.id` as the durable machine identifier because filenames and titles can change.
- Use `tags` for broad grouping such as `kg/person`, `kg/concept`, `kg/org`, or `kg/project`; do not use tags as the canonical edge type store.

## Field Rules

Read `references/relationship-schema.md` before designing new graph conventions, updating templates, or interpreting validation findings.

Read `references/edge-ontology.yaml` before adding new edge types. Prefer an existing edge unless the new edge adds a distinct analytic meaning.

Required node fields for new graph notes:

- `kg.id`
- `kg.type`

Supersession: never delete a superseded note. Set `kg.status: deprecated` and
`kg.deprecated_by: <successor kg.id>` so provenance survives while default
search hides the stale revision (see the Supersession section in
`references/relationship-schema.md`). Use `bin/search ... --include-deprecated`
to audit superseded lineage.

Required relationship fields:

- `type`
- `target`

Useful optional relationship fields:

- `target_id`
- `confidence`: `high`, `medium`, or `low`
- `evidence`: list of Obsidian links, URLs, or citation strings
- `start`
- `end`
- `status`: `current`, `historical`, `disputed`, `proposed`, or `deprecated`
- `note`

## Legacy Support

Existing notes may use this older shape:

```yaml
relationships:
  - "#part_of [[Graph Theory]]"
```

Treat it as readable legacy input, not the preferred format for new notes. When touching a note with legacy relationships, convert it to object edges if the edit is in scope.

## Scripts

Run scripts from the vault root.

Validate one note or folder:

```bash
python3 skills/knowledge-graph/scripts/validate_kg_relationships.py "path/to/note.md"
python3 skills/knowledge-graph/scripts/validate_kg_relationships.py "path/to/folder"
```

Validate the vault:

```bash
python3 skills/knowledge-graph/scripts/validate_kg_relationships.py
python3 skills/knowledge-graph/scripts/validate_kg_relationships.py --strict
python3 skills/knowledge-graph/scripts/validate_kg_relationships.py --json
```

Export triples:

```bash
python3 skills/knowledge-graph/scripts/export_kg.py --format csv --output /tmp/knowledge-graph.csv
python3 skills/knowledge-graph/scripts/export_kg.py --format json --output /tmp/knowledge-graph.json
python3 skills/knowledge-graph/scripts/export_kg.py --format jsonl
```

Analyze the graph:

```bash
python3 skills/knowledge-graph/scripts/analyze_kg.py
python3 skills/knowledge-graph/scripts/analyze_kg.py --json
```

Build or update the local search index, then search it:

```bash
bin/search query terms --limit 10
bin\search.cmd query terms --limit 10  # Windows PowerShell/CMD
python3 .agents/skills/knowledge-graph/scripts/kg_index.py --root . --json
python3 .agents/skills/knowledge-graph/scripts/kg_search.py query terms --root . --limit 10
```

Validate that the repo has not drifted from the KG search system:

```bash
git config core.hooksPath .githooks
bin/validate-kg
bin\validate-kg.cmd  # Windows PowerShell/CMD
```

`core.hooksPath` must point at `.githooks` so the KG validator runs before
commit. `validate-kg` fails when the hook path is not installed.

Record retrieval feedback when a search result was actually useful:

```bash
python3 .agents/skills/knowledge-graph/scripts/kg_feedback.py \
  --query "query terms" \
  --event read \
  --path path/from/repo/root.md \
  --success
```

The search index is local state under `.kg/`. It is rebuilt lazily by
`kg_search.py`, so it should not be committed. Dot-directories are skipped by
default except `.skills/`, which is indexed as procedural memory.

Windows gotcha: when validating a repo-local vault from outside the vault root,
prefer an absolute `--root` path such as
`python .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py --root F:\Code\Epistemic-Humility-Research\library`.
A relative `--root library` can produce false unresolved-link warnings on
Windows even when absolute-root validation passes cleanly.

Windows KG-search gotchas:

- Fresh git worktrees have their own `.kg/` local state. The project
  `.githooks/post-checkout` hook warms the repo-wide KG index automatically when
  `git worktree add` checks out into `.worktrees/` or `ehr-worktrees/`, but only
  if `core.hooksPath` points at `.githooks`. If a first search in a worktree
  still times out, let the warmup complete once with
  `python .agents/skills/knowledge-graph/scripts/kg_index.py --root . --json`
  or use a scoped search while it warms.
- Repo-wide KG search can fall back from `git ls-files` to a recursive walk and
  hit inaccessible local cache files, especially Hugging Face cache snapshots
  under `.cache/`. When that happens, rerun with a scoped root such as
  `--root library` or another narrow subtree rather than indexing the whole
  checkout.
- If the default `.kg/index.sqlite` is stale or throws SQLite constraint errors,
  avoid deleting local state as a first move. Use a scratch DB under a writable
  repo-local temp directory, for example:
  `python .agents/skills/knowledge-graph/scripts/kg_search.py "query" --root library --db .tmp/kg-search/query.sqlite --limit 12`.
- PowerShell sessions using cp1252 stdout can crash while printing KG search
  results that contain math or citation Unicode. Set
  `$env:PYTHONIOENCODING='utf-8'` before rerunning the search.

## Workflow

1. Inspect the note or folder the user names.
2. Read `references/relationship-schema.md` for conventions when creating or editing graph metadata.
3. Read `references/edge-ontology.yaml` before choosing or adding edge types.
4. Preserve user-authored prose and unrelated frontmatter.
5. Prefer canonical relationship objects for new edits.
6. Add matching `related` links for every relationship target.
7. Run `scripts/validate_kg_relationships.py` on touched files before finishing.
8. Use `scripts/export_kg.py` or `scripts/analyze_kg.py` when the user asks for reports, graph extraction, ontology drift, central nodes, unresolved targets, or analytic summaries.

## Batch Migration

Use this workflow when updating multiple existing notes, especially with small or cheaper subagents:

1. Start with 3-5 notes that share a folder, series, or failure mode.
2. Run `scripts/validate_kg_relationships.py` on the exact batch before editing.
3. Ask the subagent for proposed replacement frontmatter only; keep write control with the main agent unless the user explicitly assigns edits to the subagent.
4. Require the proposal to preserve existing `title`, `description`, `type`, `status`, `series`, `date`, and useful tags.
5. Require `kg.id`, `kg.type`, and the matching `kg/<type>` tag. For example, `kg.type: concept` requires `kg/concept`.
6. Require `related` to contain every `relationships[].target`.
7. Prefer `related_to` for conservative migration from bare wikilinks; use stronger ontology edges only when the note text clearly supports them.
8. Do not add `target_id` unless the target note was inspected and its `kg.id` is visible.
9. Apply the audited proposal locally, then rerun validation and an export/analyze smoke test.
10. If a subagent misses a repeatable rule, patch this skill or `references/relationship-schema.md` before scaling up.

Good subagent prompt constraints:

- "Do not edit files; return exact frontmatter proposals only."
- "Add `kg/<type>` to tags for every `kg.type`."
- "Convert bare wikilinks under `relationships` into object-form edges."
- "Do not invent strong factual edges; prefer `related_to` unless the note body justifies more."
- "Do not add `target_id` unless you directly inspect the target note frontmatter."

## Obsidian Notes

Obsidian Properties can store YAML, links, and lists, but nested properties are source-mode-first. This skill intentionally favors source-mode YAML objects because analysis reliability matters more than editing the graph through the Properties UI.

Use Bases for native table views over top-level fields such as `kg`, `related`, `tags`, and `aliases`, but use the scripts for typed-edge validation and analysis.
