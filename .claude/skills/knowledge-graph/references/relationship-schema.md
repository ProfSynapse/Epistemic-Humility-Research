# Relationship Schema

## Purpose

This convention keeps Obsidian notes readable while producing deterministic graph triples:

```text
source note -> relationship type -> target note
```

The source node is always the note containing the frontmatter.

## Canonical Frontmatter

```yaml
---
title: "Simulated Annealing"
aliases:
  - SA
tags:
  - kg/concept
kg:
  id: concept:simulated-annealing
  type: concept
  status: canonical
related:
  - "[[Annealing in Metallurgy]]"
  - "[[Traveling Salesman Problem]]"
relationships:
  - type: inspired_by
    target: "[[Annealing in Metallurgy]]"
    target_id: concept:annealing-in-metallurgy
    confidence: high
  - type: applied_to
    target: "[[Traveling Salesman Problem]]"
    target_id: concept:traveling-salesman-problem
    confidence: medium
---
```

## Node Metadata

`kg.id` is a durable identifier for scripts and exports. Use lowercase namespace IDs:

```yaml
kg:
  id: person:joseph-rosenbaum
  type: person
```

Recommended namespaces:

- `person`
- `org`
- `project`
- `concept`
- `work`
- `place`
- `event`
- `artifact`
- `source`
- `claim`

`kg.type` should usually match the namespace before the colon in `kg.id`.

`kg.status` is optional. Use:

- `canonical`
- `alias`
- `draft`
- `external`
- `deprecated`

## Relationships

Use one object per edge:

```yaml
relationships:
  - type: father_of
    target: "[[Benjamin Netanyahu]]"
```

Required:

- `type`: canonical edge type from `edge-ontology.yaml`
- `target`: quoted Obsidian wikilink

Optional:

- `target_id`: durable `kg.id` of the target note when known
- `confidence`: `high`, `medium`, or `low`
- `evidence`: list of Obsidian links, URLs, or citation strings
- `start`: date, year, or string
- `end`: date, year, or string
- `status`: `current`, `historical`, `disputed`, `proposed`, or `deprecated`
- `note`: short explanation

Do not put multiple target notes in one relationship object. Use separate objects:

```yaml
relationships:
  - type: sibling_of
    target: "[[Yonatan Netanyahu]]"
  - type: sibling_of
    target: "[[Iddo Netanyahu]]"
```

## Related Projection

`related` is the native Obsidian projection of relationship targets:

```yaml
related:
  - "[[Benjamin Netanyahu]]"
  - "[[Cornell University]]"
```

Every `relationships[].target` should appear in `related`. This makes native backlinks, Graph view, link autocomplete, and Bases more useful. Treat `relationships` as the source of typed truth and `related` as a convenience projection.

`related` may include additional untyped links when a note should stay visibly connected but the relationship is not yet modeled.

## Legacy Relationship Shorthand

Older notes may use:

```yaml
relationships:
  - "#part_of [[Graph Theory]]"
```

The validator and exporter can read this as legacy input. Convert it to:

```yaml
relationships:
  - type: part_of
    target: "[[Graph Theory]]"
```

## Edge Naming

Use `snake_case`, lowercase, and verbs or relational phrases:

- Good: `worked_at`, `part_of`, `influenced_by`
- Avoid: `WorkedAt`, `work-at`, `#worked_at`, `related`

Use `related_to` for intentionally weak semantic links. If a more specific relationship matters for analysis, add or choose that edge instead.

## Evidence

Use `evidence` when an edge is factual, controversial, easy to misremember, or likely to be reused in public writing:

```yaml
relationships:
  - type: founded_by
    target: "[[Ruhollah Khomeini]]"
    confidence: medium
    evidence:
      - "[[Islamic Revolutionary Guards Corps Research Note]]"
      - "https://example.org/source"
```

Use `confidence: low` for hypotheses and inferred relationships. Use `status: disputed` for contested claims.
