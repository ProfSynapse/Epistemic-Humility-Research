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
| Experiment | `experiment` | `experiment:j-space-localization-qwen3-4b` | `library/concepts/experiments/` |

Atoms are atomic: one concept per file, reused by many papers. A paper note
*references* atoms through edges; it does not redefine them.

Gaps and experiment concept atoms are graph nodes too: a gap is a verified
absence drawn from the meta-analysis, and an experiment atom can `tests` a gap
(or mechanism) and `builds_on` the papers it draws from. Operational experiment
runbooks and plans live beside governed experiment records under
`experiments/<slug>/`; they are provenance documents, not the primary library KG
surface.

## Edge vocabulary (research overlay)

Paper to entity (the research extension in `edge-ontology.yaml`):

- `proposes` / `proposed_by` : paper introduces a method/metric/dataset/term
- `uses` : paper applies an existing method
- `evaluates_on` : paper evaluates on a dataset/benchmark
- `measures` : paper reports a metric
- `studies` : paper studies a term or mechanism
- `supports` / `supported_by` : paper provides evidence for a mechanism (a claim)

Experiment to entity:

- `tests` / `tested_by` : experiment tests or addresses a gap or mechanism
- `builds_on` / `built_on_by` : experiment builds on a paper, method, or prior result

Entity lineage (generic edges, reused):

- `derived_from` (also for "extends"), `variation_of`, `required_by`, `related_to`

Mechanism nodes are `claim`-like: they carry `cause`, `effect`, `polarity`
descriptive fields, `supported_by` edges to the papers that evidence them, and
`related_to` edges to the concept atoms named in cause/effect.

### `polarity` is a closed vocabulary (enforced)

`polarity` is REQUIRED on every mechanism atom and must be one of the thirteen
values below. The vocabulary lives in the skill's
`references/edge-ontology.yaml` under `field_vocabularies.mechanism.polarity`;
the validator fails the commit on a missing, non-string, or off-vocabulary value
(codes KG120 / KG121 / KG122, severity ERROR).

| Value | Use when |
|---|---|
| `increases` | Cause raises the magnitude or rate of the effect. |
| `decreases` | Cause lowers the magnitude or rate of the effect. |
| `enables` | Cause makes the effect possible without forcing it. |
| `prevents` | Cause blocks the effect from occurring. |
| `mediates` | Cause carries or routes an effect originating elsewhere. |
| `causes` | Cause produces the effect directly (strong form of `enables`). |
| `modulates` | Cause changes the effect with no fixed sign. |
| `trades_off` | Cause improves one quantity at the measured expense of another. |
| `redistributes` | Cause reallocates a fixed quantity rather than adding or removing. |
| `limits` | Cause bounds how far the effect can go, without reducing it. |
| `complicates` | Finding confounds or undercuts an interpretation; no causal sign asserted. |
| `decouples` | Finding asserts two quantities are NOT coupled. |
| `explains` | Cause accounts for an effect observed elsewhere; explanatory, not causal-magnitude. |

The last three carry most of the program's null and confound results, so reach
for them rather than forcing a null into `decreases`. Adding a fourteenth value
is a deliberate schema change: edit the ontology and add a `changelog` entry.

### Quantified mechanisms (optional)

A mechanism may carry its effect size. All three fields are optional, but a
magnitude with no provenance is exactly the claim this program does not accept,
so `coefficient` hard-requires `coefficient_source` (KG124, ERROR).

```yaml
coefficient: 19.8                    # bare number, ERROR if non-numeric (KG123)
coefficient_units: "percentage points of answer-matching rate, PaLM 8B to 62B"
coefficient_source: "2308.03958 Section 2, Figure 2"   # table/figure/section, never a bare paper id
```

Do not backfill the qualitative atoms. Add a coefficient when the mechanism is
cited with a number in a manuscript, or when a new ingest reads one off a table.

### Bitemporal fields on `kg` (optional)

Two clocks, routinely confused. World time is when the claim HOLDS; belief time
is when WE held it. A result measured on one checkpoint stays true of that
checkpoint forever, even after we stop treating it as the current reading.

```yaml
kg:
  id: mechanism:example
  type: mechanism
  status: deprecated
  valid_from: 2026-07-24        # WORLD: the claim holds from here
  valid_until: 2026-08-01       # WORLD: absent means open-ended
  recorded_at: 2026-07-25       # BELIEF: when it entered the graph
  deprecated_by: mechanism:successor
  superseded_at: 2026-08-13     # BELIEF: when we stopped holding it
```

`superseded_at` requires `deprecated_by` (KG124, ERROR): a supersession stamp
with no successor says a claim died without saying what replaced it. Setting
`deprecated_by` without `superseded_at` is a warning (KG125), not a failure.

All dates accept `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, or an ISO timestamp, quoted or
unquoted (KG123, ERROR otherwise).

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
python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py library
```

New papers are folded in with the `kg-ingest` skill, which emits this exact
shape. The map of all atoms is `library/concepts/README.md`; governed experiment
records are indexed in `experiments/REGISTRY.md`.
