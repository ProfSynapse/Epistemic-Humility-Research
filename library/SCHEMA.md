# Knowledge-graph schema (library vault)

The library is an Obsidian-style knowledge graph. It uses the **canonical graph
schema** defined by the vendored `knowledge-graph` skill (`kg` node metadata +
typed `relationships` objects + a `related` projection), and it follows the
design idea of **Agents-K1 (arXiv:2606.13669)**: capture entities, claims,
evidence, mechanisms, and method lineages as typed nodes and edges rather than
reducing papers to abstracts and flat `cites` edges.

The format and tooling are authoritative in the skill; read those before
changing conventions:

- `.agents/skills/knowledge-graph/references/relationship-schema.md` : the `kg` /
  `relationships` / `related` frontmatter contract.
- `.agents/skills/knowledge-graph/references/edge-ontology.yaml` : the governed
  edge vocabulary (generic edges + the research extension).
- `.agents/skills/knowledge-graph/scripts/` : `validate`, `export`, `analyze`.

This file records only the **domain overlay** for the epistemic-humility library.

## Node kinds and `kg.id` namespaces

Every graph note carries `kg: {id, type, status}` and a `kg/<type>` tag. `kg.id`
is `namespace:slug` and survives renames.

| Kind | `kg.type` | `kg.id` example | Lives in |
|------|-----------|-----------------|----------|
| Paper | `paper` | `paper:2305.18290` | `library/notes/<arxiv>--<slug>.md` |
| Method / algorithm | `method` | `method:direct-preference-optimization` | `library/concepts/methods/` |
| Metric | `metric` | `metric:expected-calibration-error` | `library/concepts/metrics/` |
| Dataset / benchmark | `dataset` | `dataset:selfaware` | `library/concepts/datasets/` |
| Model | `model` | `model:instructgpt` | `library/concepts/models/` |
| Term of art | `term` | `term:knowledge-boundary` | `library/concepts/terms/` |
| Mechanism (cause -> effect) | `mechanism` | `mechanism:ft-unknown-facts-drives-hallucination` | `library/concepts/mechanisms/` |
| Gap (verified literature absence) | `gap` | `gap:4-probe-transfer` | `library/concepts/gaps/` |
| Experiment (note) | `experiment` | `experiment:gradient-probe-coherence` | `experiment/notes/` |

Atoms are atomic: one concept per file, reused by many papers. A paper note
*references* atoms through edges; it does not redefine them.

Gaps and experiments are graph nodes too: a gap is a verified absence drawn from
the meta-analysis, and an experiment note `tests` a gap (or mechanism) and
`builds_on` the papers it draws from. Experiment notes live under
`experiment/notes/` (outside `library/`), so validation must include both trees
(see Tooling).

## Edge vocabulary (research overlay)

Paper to entity (the research extension in `edge-ontology.yaml`):

- `proposes` / `proposed_by` : paper introduces a method/metric/dataset/term
- `uses` : paper applies an existing method
- `evaluates_on` : paper evaluates on a dataset/benchmark
- `measures` : paper reports a metric
- `studies` : paper studies a term or mechanism
- `supports` / `supported_by` : paper provides evidence for a mechanism (a claim)

Experiment to entity (the experiment-note overlay):

- `tests` / `tested_by` : experiment tests or addresses a gap or mechanism
- `builds_on` / `built_on_by` : experiment builds on a paper, method, or prior result

Entity lineage (generic edges, reused):

- `derived_from` (also for "extends"), `variation_of`, `required_by`, `related_to`

Mechanism nodes are `claim`-like: they carry `cause`, `effect`, `polarity`
descriptive fields, `supported_by` edges to the papers that evidence them, and
`related_to` edges to the concept atoms named in cause/effect.

## Edge object shape

```yaml
relationships:
  - type: proposes
    target: "[[kahneman-tversky-optimization]]"
    target_id: method:kahneman-tversky-optimization
    confidence: high          # high | medium | low (optional)
    evidence: ["Table 2"]      # links / citations / table-figure refs (optional)
related:
  - "[[kahneman-tversky-optimization]]"   # projection of every edge target
```

`evidence` is well suited to research edges: cite the exact table/figure/section.

## Tooling (run from repo root)

```bash
# library only (atoms + papers + gaps)
python3 .agents/skills/knowledge-graph/scripts/analyze_kg.py  --root library
python3 .agents/skills/knowledge-graph/scripts/export_kg.py   --root library --format csv --output /tmp/eh-kg.csv
# validate library AND experiment notes (experiment/ lives outside library/, so
# pass both trees as positional paths)
python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py library experiment/notes
```

New papers are folded in with the `kg-ingest` skill, which emits this exact
shape. The map of all atoms is `library/concepts/README.md`; experiment notes are
indexed in `experiment/notes/README.md`.
