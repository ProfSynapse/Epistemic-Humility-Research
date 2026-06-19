# Research: Web / Shareable Interactive Visualization for the Epistemic-Humility Knowledge Graph

> PACT Prepare-phase deliverable. Research only — no application code is added to the repo
> beyond this document. Converter snippets below are sketches for the Architect/Code phases,
> not committed scripts. Tool versions and capabilities verified against 2026 sources (cited
> inline); the external tool landscape is decay-prone, so uncertainty is bumped +1 and
> currency caveats are called out where they bite.

## Executive summary

For our graph — ~272 typed nodes, ~310 logical typed edges, governed edge ontology, sparse
confidence metadata, currently-empty status/evidence — the dominant constraint set by the user
is **a self-contained, zero-infrastructure artifact** you can drop into a paper's supplementary
materials or hand to a collaborator who just double-clicks an HTML file. That single constraint
is decisive and reorders the whole field.

**Primary recommendation: Cytoscape.js**, data baked into one static `index.html` via a ~60-line
glue script fed by `export_kg.py --format json`. It is the best fit because our requirements are
*typed-edge semantics + per-element metadata styling/filtering at small scale*, not raw rendering
throughput — and Cytoscape.js maps node/edge `data()` fields directly to color, labels, and
selector-based filters, which is exactly our `source_type` / `edge_type` / `confidence` model.

**Close alternative (primary tier): sigma.js + graphology**, and — for a no-code path on top of
that same engine — **Gephi Lite v1.0**, which can publish a graph as a shareable permalink or an
embeddable `<iframe>`. Choose this lane if you'd rather not maintain even a small glue script and
are willing to convert to GEXF/GraphML once.

**Secondary tier (only if you will host / run a process): Neo4j (Browser/Bloom)** and
**Graphistry (GPU)** — powerful explorers, but both need a running server, so they fail the
"email a file" test and are subordinated here, as instructed.

**Do not plan around Kùzu.** KùzuDB was archived and its company acquired by Apple in October
2025; the open-source repo is no longer maintained. It is documented below as a *cautionary
note plus a bridge pointer* (the `bighorn` fork) rather than a live recommendation.

---

## Background and constraints (grounded in our actual graph)

The dispatch and a follow-up steer from the team-lead fix the requirements:

- **Dominant constraint (locked):** self-contained static HTML/JS, **no running server**.
  Rationale: "embeddable in a paper / supplementary materials" and "sent to collaborators" both
  demand a zero-infra artifact. Static-export approaches are therefore the **primary tier**;
  server-backed tools are a clearly-labeled **secondary tier**.
- **Goal spans** exploration + analysis + presentation. Obsidian-native tools are
  **de-prioritized** (user did not pick them); Obsidian Publish gets a one-line mention only.
- **Coordination boundary:** the Python/notebook analysis stack is owned by `preparer-prog`.
  This doc cross-references Python bindings where a web tool has one but does not evaluate the
  notebook stack.

### What the data actually looks like

Run against the live vault (`export_kg.py --root library --format json`), not assumed:

| Fact | Value | Why it matters for tool choice |
|------|-------|--------------------------------|
| Exported triples | **619** rows | Edges are emitted **bidirectionally** (e.g. `proposes` 45 + `proposed_by` 45). A converter must **dedupe inverse pairs** to ~310 undirected/canonical-direction edges, or the graph renders doubled. |
| Distinct node IDs in export | **182** | Fewer than the ~272 notes: many concept atoms have **no edges yet** and so never appear in a triple export. If you want isolated nodes shown, the converter must also read the note set, not only the triples. |
| Node types (`source_type`) | paper, mechanism, method, metric, dataset, model, term | 7-way categorical → **node color/shape by type**. Every candidate supports this. |
| Edge types (`edge_type`) | `related_to` (265), `supported_by`/`supports` (59/59), `proposed_by`/`proposes` (45/45), `uses` (35), `studies` (32), `evaluates_on`/`measures` (28/28), `derived_from` (16), `variation_of` (4), `required_by` (3) | `related_to` is ~43% of rows and is the **weak catch-all**; the typed research edges are the semantically interesting ones. A good viz must **filter by edge type** (e.g. hide `related_to` to see the proposes/supports skeleton). |
| `confidence` | 104 rows `high`, 515 empty | Display **when present**; do not build the UX around it — it is sparse. |
| `status` | **empty on all 619 rows** | The "show status on hover/filter" requirement is currently **aspirational**. Support it generically (render any present field) but do not weight a tool on a status-specific feature. |
| `evidence` | **empty on all 619 rows** | Same as status: render-if-present, don't over-weight. (`evidence` is a list; CSV joins it with `;`.) |
| Scale | ~272 nodes / ~310 edges | **Small.** WebGL throughput is irrelevant here. This *demotes* the headline selling point of sigma.js/Graphistry (large-graph rendering) and *promotes* per-element semantics, styling ergonomics, and packaging. |

**Decision implication:** at this scale the differentiator is **how cleanly a tool maps our typed
fields to color/label/filter and how easily it bakes into one shareable file** — not rendering
performance. This is the lens for every score below.

### Exact export schema (the converter's input contract)

`export_kg.py` emits these fields per triple in CSV/JSON/JSONL
(`.agents/skills/knowledge-graph/scripts/export_kg.py`, `CSV_FIELDS`):

```
source_path, source, source_id, source_type, edge_type,
target, target_id, target_path, confidence, status,
start, end, evidence, legacy
```

JSON/JSONL emit the same fields as objects (`evidence` stays a list in JSON; CSV joins with `;`).
`source_id` / `target_id` are stable `namespace:slug` identifiers (e.g. `paper:2506.09038`,
`dataset:abstentionbench`) and are the natural node keys. `source_type` is present; **target type
is not a column** — the converter should infer a target's type from the `target_id` namespace
prefix or from the row where that node appears as a `source`.

---

## Methodology

- Primary sources: official docs/repos/release blogs for each tool; npm for current versions;
  context7 for Cytoscape.js styling/selector API. WebSearch for 2026 status/version currency.
- Ground truth: the live `export_kg.py` JSON export of `library/`, plus `library/SCHEMA.md` and
  `edge-ontology.yaml`, to score *fit to our data* rather than generic capability.
- Evaluation axes (from the dispatch): ingestion fit; typed edges + edge labels + node-type
  coloring; edge-metadata display (confidence/status/evidence) on hover/filter; interactivity
  (filter/search/expand-neighbors); shareability/embeddability (static HTML vs server); learning
  curve; cost/licensing; fit at ~272-node scale.

---

## Comparison matrix

Tiering reflects the locked dominant constraint (static, no server). Scores: ●●● strong /
●●○ adequate / ●○○ weak, judged **for this graph at this scale**.

| Tool (version) | Tier | Ingest our triples | Typed edges + labels + type-color | Metadata on hover/filter | Interactivity | Shareable as static file | Learning curve | Cost / license | Fit @ ~272 |
|---|---|---|---|---|---|---|---|---|---|
| **Cytoscape.js** 3.34.0 | **Primary** | ●●● JSON `elements` via small glue | ●●● `data()`→color/label, selectors per edge type | ●●● `data()` selectors + `cytoscape-popper` tooltips | ●●● filter/search/neighborhood built-in | ●●● single HTML, data inlined | ●●○ JS, but tiny app | ●●● MIT, free | ●●● ideal |
| **sigma.js v3 (+v4 alpha) + graphology** | **Primary** | ●●○ needs graphology build / GEXF | ●●● color/label/type via reducers | ●●○ hover via reducers; you write the panel | ●●● pan/zoom/hover; filter via graphology | ●●● single HTML, data inlined | ●●○ renderer-only, more wiring | ●●● MIT, free | ●●○ overkill (WebGL for large graphs) |
| **Gephi Lite v1.0** (no-code, sigma-based) | **Primary** | ●●○ import GEXF/GraphML (convert once) | ●●● UI: color by attr, edge styling | ●●○ attribute panels + filters in UI | ●●● filters/layout/search in UI | ●●● **permalink + iframe embed** | ●●● no code at all | ●●● open-source (Gephi) | ●●● great for present/share |
| **vis-network** 10.1.0 | Primary-ish | ●●● nodes/edges arrays via glue | ●●○ color/label yes; edge-type styling manual | ●●○ `title` tooltips; filtering manual | ●●○ drag/zoom; less filter machinery | ●●● single HTML | ●●● easiest API | ●●● (A)GPL/MIT dual | ●●○ fine, fewer semantics |
| **AntV G6** 5.1.1 | Primary-ish | ●●○ JSON via glue | ●●● rich styling/themes, edge labels | ●●○ tooltip/legend plugins | ●●● plugins: filter/legend/minimap | ●●○ single HTML (heavier bundle) | ●○○ steeper, docs partly zh | ●●● MIT, free | ●●○ powerful but heavy |
| **D3-force** (d3 v7) | Fallback | ●●○ raw JSON, you build everything | ●●○ all manual | ●○○ all manual | ●○○ all manual | ●●● single HTML | ●○○ build from scratch | ●●● ISC/BSD | ●●○ max control, max effort |
| **Neo4j Browser / Bloom** 2.34 | **Secondary (server)** | ●●○ load via CSV `LOAD CSV`/import | ●●● typed rels native, styling in Bloom | ●●● properties panel, Cypher filter | ●●● best-in-class explore/expand | ●○○ **needs running DB + app** | ●●○ Cypher + import step | ●●○ Community free; Aura/Bloom tiers | ●●● but heavy for 272 |
| **Graphistry (GPU)** | **Secondary (server)** | ●●● PyGraphistry upload (CSV/df) | ●●● auto styling, encodings | ●●● rich hover/encodings | ●●● strong explore | ●○○ **hosted/live embed, not a file** | ●●○ via PyGraphistry | ●○○ paid (~$83–167/mo) + free tier | ●●○ built for huge graphs |
| **Kùzu + kuzu-explorer** | **N/A — abandoned** | — | — | — | — | ●○○ needs Docker/server anyway | — | MIT but **unmaintained (archived Oct 2025)** | — |
| **Linkurious Ogma / ReGraph** | Secondary (commercial) | ●●● flexible | ●●● excellent | ●●● excellent | ●●● excellent | ●●○ embeddable in your app | ●●○ SDK | ●○○ **commercial** (ReGraph ~$10/user/mo; Ogma quote) | ●●● overkill + cost |
| **Obsidian Publish** | Mentioned only | n/a (vault notes) | ●●○ generic graph view | ●○○ not edge-typed metadata UX | ●●○ vault graph | ●●○ **hosted site (subscription)** | ●●● none | ●○○ paid Obsidian service | ●●○ not the typed-KG presenter you want |

---

## Findings (detail)

### Primary tier — static, no server

#### 1. Cytoscape.js 3.34.0 — recommended primary

- **Currency:** 3.34.0 released June 2026; actively maintained, frequent releases
  ([releases](https://github.com/cytoscape/cytoscape.js/releases),
  [npm](https://www.npmjs.com/package/cytoscape)). MIT.
- **Fit to our data:** styles are a JSON array of `{selector, style}`. Map our fields directly:
  - node color/shape by type: `selector: 'node[type = "paper"]'` etc., or
    `'background-color': 'mapData(...)'`/category mapping on `data(type)`;
  - edge label = the relationship: `'label': 'data(edge_type)'`;
  - filter by edge type with data-attribute selectors:
    `cy.edges('[edge_type = "proposes"]')`, hide the `related_to` noise with
    `cy.edges('[edge_type = "related_to"]').hide()`;
  - confidence styling when present: `'[confidence = "high"]' → thicker/opaque edge`.
  (All confirmed against the Cytoscape.js style + selectors docs via context7.)
- **Metadata on hover:** the `cytoscape-popper` extension binds a tooltip to any element, so a
  hover panel can show `source → edge_type → target`, plus `confidence` / `status` / `evidence`
  *when those fields are non-empty* (today only confidence is). Search by adding a text box that
  runs `cy.nodes('[id *= query]')`.
- **Shareability:** the whole thing is one `index.html` with Cytoscape from a CDN/inlined and the
  graph JSON inlined as a `const elements = [...]`. Double-click to open; email it; drop it in
  `/supplementary/`. No server. This is the cleanest match to the locked constraint.
- **Cost/curve:** free; a working app is well under 100 lines. Slight curve vs vis-network, but
  it buys the typed-selector model we specifically need.

#### 2. sigma.js v3 (v4 in alpha) + graphology — close alternative

- **Currency:** MIT; renderer built on graphology; v4 is alpha, v3 is the stable line
  ([sigmajs.org/docs](https://www.sigmajs.org/docs/),
  [repo](https://github.com/jacomyal/sigma.js/)). Ships extensions `@sigma/node-border`,
  `@sigma/node-image`, `@sigma/edge-curve`.
- **Fit:** explicitly a *renderer + data layer*, **not** a batteries-included analysis lib — that
  split is a strength for typed data flows. Node/edge appearance via reducer functions keyed on
  attributes → easy type coloring and per-edge styling.
- **Trade-off for us:** sigma's headline is WebGL rendering of *thousands* of nodes. At ~272 nodes
  that strength is wasted, and you write more wiring (the hover panel, filters) yourself than in
  Cytoscape.js. Still bakes into one static HTML. Pick it if you're already in this ecosystem or
  want the no-code Gephi Lite path below.

#### 3. Gephi Lite v1.0 — the no-code primary path (sigma-based)

- **Currency:** v1.0 released Oct 2025; web app, open-source Gephi ecosystem, uses sigma.js +
  graphology under the hood ([announcement](https://gephi.wordpress.com/2025/10/08/gephi-lite-v1/),
  [repo](https://github.com/gephi/gephi-lite)).
- **Why it matters here:** it directly answers "drop in a graph, get an interactive, *shareable*
  page." It supports **permalinks** ("share Gephi graphs as if they were web documents") and
  **iframe embedding** ("embed Gephi Lite directly inside web pages"), plus in-UI color-by-attribute,
  filters, layout, and search — no code. Import is graph-file based (GEXF/GraphML), so you convert
  our triples **once** to GEXF and never touch JS.
- **Caveat:** permalink/iframe sharing leans on hosted Gephi Lite infrastructure rather than a
  truly offline single file; a planned read-only "Gephi Viewer" is future work. For a paper's
  *offline* supplementary file, Cytoscape.js is more self-contained; for a quick *shareable link*
  to collaborators with zero code, Gephi Lite is the fastest route. Related: **Retina**
  (Gephi's WebPublish) similarly turns a GEXF into a hosted, embeddable interactive view.

#### 4 & 5. vis-network 10.1.0 / AntV G6 5.1.1 — viable, not preferred

- **vis-network 10.1.0** (active; ~468k weekly downloads;
  [npm](https://www.npmjs.com/package/vis-network)): the gentlest API and trivially produces a
  single static HTML. Node coloring/labels are easy; `title` gives hover tooltips. But edge-type
  styling and filtering are more manual, and it has a weaker typed-selector model than Cytoscape.js
  — so it under-serves our "filter by edge type / style by confidence" need. Good *fallback if the
  team wants the absolute lowest-effort code path.*
- **AntV G6 5.1.1** (MIT; Rust/WebGPU layouts;
  [npm](https://www.npmjs.com/package/@antv/g6), [G6 5.0 overview](https://yanyanwang93.medium.com/g6-5-0-a-professional-and-elegant-graph-visualization-engine-11bba453ff4d)):
  the most feature-rich (themes, legend/minimap/tooltip plugins, even 3D), but heavier bundle,
  steeper curve, and parts of the ecosystem are documented in Chinese. Power we don't need at 272
  nodes; it would slow the "ship a small file" goal.

#### Fallback. D3-force

Maximum control, but you build node coloring, edge labels, tooltips, filtering, and search from
scratch. Only choose if the visualization needs a bespoke layout/encoding no library offers.
For this typed-but-small graph it is more effort than value.

### Secondary tier — only if you will host / run a process

These are *subordinated, not dropped*, per the steer. They are strong explorers but fail the
"email a self-contained file" test.

- **Neo4j Browser / Bloom 2.34** ([Bloom docs](https://neo4j.com/docs/bloom-user-guide/current/),
  [graph-viz tools](https://neo4j.com/docs/getting-started/graph-visualization/graph-visualization-tools/)):
  best-in-class interactive exploration (expand-neighbors, Cypher filtering, properties panel) and
  typed relationships are native. Path: `export_kg.py --format csv` → `LOAD CSV` / `neo4j-admin
  import` → explore in Browser/Bloom. But it requires a running database and the Browser/Bloom app;
  Bloom hosted at bloom.neo4j.io or via Aura. Use this if you want a *live analysis console* for
  yourself, not a shareable artifact. (No evidence Bloom is deprecated in 2026.)
- **Graphistry (GPU)** ([graphistry.com](https://www.graphistry.com/),
  [PyGraphistry](https://github.com/graphistry/pygraphistry)): GPU-accelerated, no-code upload of
  CSV/dataframes, rich encodings and live-embeddable visualizations. But it is a hosted service
  (managed GPU or your own server; ~$83–167/mo plus a limited free tier), built for graphs far
  larger than ours. Note: **PyGraphistry is a Python binding** — flag for `preparer-prog` as the
  cross-over point if the program ever wants GPU exploration from a notebook; it is out of scope
  for the static-file mission here.
- **Linkurious Ogma / ReGraph** (commercial SDKs; ReGraph ~$10/user/mo, Ogma by quote —
  [Capterra/ReGraph](https://www.capterra.com/p/202755/ReGraph-graph-visualization-for-React-developers/reviews/),
  [Ogma](https://qwiery.com/graphviz/ogma/)): excellent on every technical axis, but commercial
  cost is unjustified for a 272-node research graph when MIT options cover the need.

### Cautionary note — Kùzu / kuzu-explorer (do not adopt)

The dispatch listed Kùzu + kuzu-explorer as an embeddable, no-server candidate. **That is no
longer accurate.** Apple acquired Kùzu Inc. in October 2025; the KùzuDB GitHub repo was archived
~Oct 10 2025, the website went offline, and the maintainers stated they will no longer support
KùzuDB ([The Register](https://www.theregister.com/2025/10/14/kuzudb_abandoned/),
[BigGo](https://biggo.com/news/202510130126_KuzuDB-embedded-graph-database-archived),
[BetaKit](https://betakit.com/apple-strikes-deal-to-acquire-canadian-database-software-startup-kuzu/)).
Adopting an archived DB for a multi-year research program is a maintainability risk. Community
forks exist (Kineviz **`bighorn`**; "Ladybug" also mentioned). If the program later wants an
*embedded, queryable* graph store that bridges to `preparer-prog`'s Python stack, evaluate
`bighorn` (or DuckDB-PGQ / a maintained alternative) at that time — but that is a *database*
choice, not the *visualization-artifact* choice this mission is about. Keeping it out of the
recommended set is the right call.

### Obsidian Publish (mentioned only)

De-prioritized by the user. It can publish the vault with a generic graph view, but it is a paid
hosted Obsidian service and does **not** present *typed edges with confidence/status/evidence* the
way our governed ontology deserves. Not the right presenter for this graph.

---

## Recommendation (ranked)

1. **Cytoscape.js (static single-file).** Best fit: typed `data()`→style/selector model maps our
   `source_type`/`edge_type`/`confidence` exactly, `cytoscape-popper` covers metadata-on-hover,
   built-in filter/search/neighborhood, MIT, and it bakes into one offline HTML you can put in a
   paper's supplementary materials or email. Small glue script required.
2. **Gephi Lite v1.0 (no-code) or sigma.js+graphology (coded).** Same static/shareable property
   via the sigma ecosystem. Choose **Gephi Lite** if you want zero code and are happy sharing via
   permalink/iframe (convert to GEXF once); choose **sigma.js** if you want a hand-built single
   file and are already in that stack. (Retina is the Gephi web-publish variant for a hosted
   embeddable view.)
3. **Neo4j Browser/Bloom** *(secondary, server)* for a live personal analysis console;
   **Graphistry** *(secondary, server/hosted)* if GPU exploration is ever wanted (its
   PyGraphistry binding is the hand-off point to `preparer-prog`).

### Concrete next step

```
python3 .agents/skills/knowledge-graph/scripts/export_kg.py \
    --root library --format json --output /tmp/eh-kg.json
#   → run a small converter (see sketch) → write a single static index.html (Cytoscape.js)
```

**Glue/converter needed (sketch only — do not commit; for Architect/Code phase).** It must:

1. read the triples JSON;
2. **dedupe inverse edge pairs** (drop one of `proposes`/`proposed_by`, `supports`/`supported_by`,
   `measures`/`measured_by`, `evaluates_on`/`evaluation_set_for`, `studies`/`studied_by`,
   `derived_from`/`source_of`, etc.) so edges aren't doubled;
3. build the node set from both `source_id` and `target_id` (and optionally the full note list, to
   include the ~90 edge-less atoms), inferring target type from the `target_id` namespace prefix;
4. emit Cytoscape `elements` JSON:

```js
// pseudo-output the converter produces, then inlines into index.html
const elements = [
  { data: { id: "paper:2506.09038", label: "AbstentionBench", type: "paper" } },
  { data: { id: "dataset:abstentionbench", label: "abstentionbench", type: "dataset" } },
  { data: { id: "e1", source: "paper:2506.09038", target: "dataset:abstentionbench",
            edge_type: "proposes", confidence: "high",
            status: "", evidence: "" } },   // status/evidence empty in current data
  // ...
];
// style: node color by data(type); edge label = data(edge_type);
// selectors: edges('[edge_type="related_to"]').hide() to reveal the typed skeleton;
// cytoscape-popper tooltip prints source→edge_type→target (+ confidence when present).
```

A symmetric GEXF converter would feed the Gephi Lite / sigma path instead (same dedupe + type
inference, written as `<node>`/`<edge>` with `<attvalue>` for type/edge_type/confidence).

---

## Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Tool/version drift (landscape decays fast) | High | Low–Med | Versions cited with dates; re-verify at Code time; all primary picks are MIT/active. |
| Building UX around status/evidence that is currently empty | Med | Med | Render metadata **generically (if-present)**; don't gate features on status/evidence until the graph populates them. |
| Doubled edges from bidirectional export | High if unhandled | Med | Converter **must** dedupe inverse pairs (listed above). |
| `related_to` noise (43% of edges) dominates the view | High | Low | Default-hide `related_to`; toggle in UI. |
| Picking a server tool by habit (Neo4j/Graphistry) and breaking shareability | Med | High | Locked constraint: primary tier is static-file only; server tools are explicitly secondary. |
| Adopting Kùzu from the original candidate list | Was high | High | Documented as abandoned; excluded from recommendation. |

## Sources

- Cytoscape.js: [js.cytoscape.org](https://js.cytoscape.org/),
  [releases](https://github.com/cytoscape/cytoscape.js/releases),
  [npm](https://www.npmjs.com/package/cytoscape), styling/selectors via context7
  `/cytoscape/cytoscape.js`.
- sigma.js: [docs](https://www.sigmajs.org/docs/), [repo](https://github.com/jacomyal/sigma.js/).
- Gephi Lite v1.0: [announcement](https://gephi.wordpress.com/2025/10/08/gephi-lite-v1/),
  [repo](https://github.com/gephi/gephi-lite).
- vis-network: [npm 10.1.0](https://www.npmjs.com/package/vis-network),
  [repo](https://github.com/visjs/vis-network).
- AntV G6: [npm 5.1.1](https://www.npmjs.com/package/@antv/g6),
  [G6 5.0 overview](https://yanyanwang93.medium.com/g6-5-0-a-professional-and-elegant-graph-visualization-engine-11bba453ff4d).
- Neo4j Bloom/Browser: [Bloom 2.34 docs](https://neo4j.com/docs/bloom-user-guide/current/),
  [graph-viz tools](https://neo4j.com/docs/getting-started/graph-visualization/graph-visualization-tools/).
- Graphistry: [graphistry.com](https://www.graphistry.com/),
  [PyGraphistry](https://github.com/graphistry/pygraphistry).
- Linkurious Ogma / ReGraph:
  [ReGraph (Capterra)](https://www.capterra.com/p/202755/ReGraph-graph-visualization-for-React-developers/reviews/),
  [Ogma](https://qwiery.com/graphviz/ogma/).
- Kùzu status: [The Register](https://www.theregister.com/2025/10/14/kuzudb_abandoned/),
  [BigGo](https://biggo.com/news/202510130126_KuzuDB-embedded-graph-database-archived),
  [BetaKit (Apple acquisition)](https://betakit.com/apple-strikes-deal-to-acquire-canadian-database-software-startup-kuzu/).
- Our graph: live `export_kg.py --root library --format json`;
  `library/SCHEMA.md`; `.agents/skills/knowledge-graph/references/edge-ontology.yaml`.
