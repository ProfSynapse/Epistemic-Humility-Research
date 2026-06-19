# Programmatic / Notebook KG Visualization + Analysis Stack

Research deliverable (PACT Prepare). Author: `preparer-prog`. Date: 2026-06-19.
Scope: the **Python / Jupyter** side of exploring, analyzing, and presenting the
Epistemic-Humility typed knowledge graph. The browser/shareable side is a
separate deliverable owned by `preparer-web`; this doc cross-references **Kùzu**
(the one shared tool) but does not duplicate the web-tool matrix.

> **Uncertainty posture (+1 per dispatch):** the external graph-library landscape
> is open-ended and decay-prone. Every current-version / maintenance claim below
> is dated and cited. Re-verify before pinning versions; several candidates here
> are inactive or were acquired/abandoned in the last 12 months.

---

## 1. Executive Summary

For our graph (~272 notes; ~182 of them currently appear in edges, ~310 logical
edges after inverse-pair dedup, a **typed directed multigraph** of paper→concept
and concept→concept edges that *can* carry `confidence` / `status` / `evidence` /
temporal attributes but mostly do not yet, see the data-shape note below), the
recommended stack is:

| Layer | Recommendation | Why |
|-------|----------------|-----|
| **Graph core** | **`networkx`** (`MultiDiGraph`) | Matches our export 1:1 (typed parallel edges + arbitrary edge attrs), native `from_pandas_edgelist`, and now ships **native Louvain *and* Leiden** community detection. |
| **Notebook renderer** | **`ipysigma`** (primary) | Actively maintained, purpose-built for networkx in Jupyter, maps node color (node type) and edge color/type (edge type), the two channels our data actually populates today, without flattening parallel edges; exports standalone HTML. |
| **Publication renderer** | **`matplotlib` via `nx.draw` + `netgraph`** (static) / **`plotly` graph_objects** (interactive figure) | Vector (SVG/PDF) output for the paper; plotly for an interactive HTML figure when a static image is too dense. |
| **Analysis layer** | **`networkx` algorithms** + **`igraph`/`leidenalg`** only if scale demands | Centrality, community, lineage path-tracing, all the things `analyze_kg.py` does *not* compute. igraph/leidenalg is a fallback for speed, not a baseline need at this scale. |
| ~~Embeddable Cypher/graph-DB layer~~ | **NOT recommended** | **Kùzu (the obvious candidate) is dead**, Apple acquired Kùzu Inc. (Oct 2025), the OSS repo is archived, maintainers dropped it (see §7). networkx traversal already covers our lineage needs; no embedded graph-DB is warranted. |

> **Data-shape constraints (verified against the live export, read before §3):**
> - **619 triples, but stored as inverse PAIRS** (`proposes` + `proposed_by`, etc.) ≈ **~310 logical edges**. The load step MUST dedupe inverse pairs or every centrality/community metric is computed on a **doubled** graph and skewed. See §2.3 and the §6 snippet.
> - **Edge metadata is sparse today:** `confidence` is 104 `high` / 515 empty; `status` and `evidence` are **empty on all 619 rows**. So lead the visual recommendation with **node-type color + edge-type**; encode confidence/status/evidence only *if present* (they will largely have nothing to show yet).
> - **Only 182 distinct node IDs appear in edges** vs ~272 notes, **~90 atoms are edge-less** and will not appear unless you also load the note list as standalone nodes (see §2.4).

**One-line rationale:** at our scale the bottleneck is never performance, it is
**fidelity**, preserving typed parallel edges through the load→analyze→render
path *and* not doubling the graph via inverse-pair edges. `networkx` + `ipysigma`
keeps the typed structure intact, is actively maintained, and needs no
compiled-from-source dependencies.

---

## 2. What We Are Loading (ground truth, not boilerplate)

Read directly from the repo before recommending anything:

- `.agents/skills/knowledge-graph/scripts/export_kg.py`
- `.agents/skills/knowledge-graph/scripts/kg_common.py` (the `Triple` dataclass)
- `.agents/skills/knowledge-graph/scripts/analyze_kg.py`
- `library/SCHEMA.md`

### 2.1 The export is a triple list with 14 columns

`export_kg.py` emits one row **per typed edge** (CSV / JSON / JSONL) via
`Triple.as_dict()`. The exact fields (`kg_common.py:116-132`):

```
source_path, source, source_id, source_type,
edge_type,
target, target_id, target_path,
confidence, status, start, end, evidence, legacy
```

Key consequences for tool selection:

- **It is a directed multigraph.** A single paper can have *multiple distinct
  typed edges to the same concept* (e.g. a paper both `uses` and `evaluates_on`
  the same dataset node). Any renderer that collapses parallel edges between a
  node pair **loses edge types**, this is the disqualifying test.
- **Edges *can* be attributed, but the metadata is SPARSE today.** The schema
  allows `confidence` (`high|medium|low`), `status`
  (`current|historical|disputed|proposed|deprecated`), `evidence` (a *list* of
  table/figure refs), and temporal `start`/`end`. **In the current export
  (619 triples): `confidence` = 104 `high` / 515 empty; `status` and `evidence`
  are empty on *all* rows.** So the renderer must support binding these to visual
  channels, but the *default* visual encoding should lead with node-type color
  and edge-type and treat confidence/status/evidence as **if-present** overlays,
  they have little to render yet. Re-check the populated fraction at adoption time.
- **Nodes are typed.** `source_type` / `target_type` ∈ `{paper, method, metric,
  dataset, model, term, mechanism}` (`library/SCHEMA.md`). Node color should
  encode type.
- **Targets may be unresolved.** `target_path == ""` means the wikilink did not
  resolve to a note (`analyze_kg.py` reports these as `unresolved_targets`). The
  load step must decide whether to materialize a placeholder node or drop the edge.
- **Stable identity is `*_id`** (`namespace:slug`, survives renames), with the
  human label in `source` / `target`. Use `source_id`/`target_id` as the graph
  node key, fall back to `source`/`target` when the id is empty (this is exactly
  the `node_key(value, fallback)` rule `analyze_kg.py:13-14` already uses, match it).

### 2.2 What `analyze_kg.py` ALREADY computes (do not duplicate)

`analyze_kg.py` returns (`:39-50`): `graph_notes`, `edge_count`, `edge_types`
(histogram), `top_degree` / `top_outgoing` / `top_incoming` (degree only),
`orphan_nodes`, `unresolved_targets`, `legacy_edges`, `scan_findings`.

So the new stack should **extend**, not re-implement, with the analyses
`analyze_kg.py` cannot give:

| Already in `analyze_kg.py` | Gap the new stack fills |
|---|---|
| Edge-type histogram | (covered) |
| Degree (in/out/total) ranking | **Betweenness / eigenvector / PageRank / Katz** centrality (which nodes are *structurally* central, not just high-degree) |
| Orphan nodes | **Connected components**, **bridge/articulation** detection, **k-core** decomposition |
| (none) | **Community detection** (Louvain / Leiden) over the concept graph |
| (none) | **Lineage / ancestry path tracing** along `derived_from` / `variation_of` (e.g. "what is the method ancestry of DPO?") |
| Flat text report | **Interactive + publication-quality figures** |

This split is the core "what extends vs duplicates" answer requested by the mission.

### 2.3 Inverse-pair edges MUST be deduped (or every metric is doubled)

The export emits **619 triples**, but the ontology stores many relationships as
**inverse pairs**, e.g. a paper's `proposes` edge to a method is mirrored by the
method's `proposed_by` edge back to the paper (`supports`/`supported_by` likewise,
per `library/SCHEMA.md`). So the 619 triples represent only **~310 logical edges**.

This is a correctness trap, not a cosmetic one: if you load all 619 rows as
distinct directed edges, the graph is **doubled**, and **every** degree,
centrality, community, and component metric is skewed. Handle it explicitly:

- **Build a directed `MultiDiGraph` from the raw rows** for direction-aware views
  and lineage tracing (direction matters for `derived_from`/`proposes`).
- **For undirected structural analysis** (centrality, community, components),
  **collapse inverse pairs first**: canonicalize each edge to one representative
  per logical relationship (e.g. drop the `*_by` inverse half, or project to an
  undirected `Graph` so the pair becomes a single undirected edge). Decide the
  canonical direction per ontology pair and document it.

The §6 snippet shows a concrete inverse-pair dedup using an explicit inverse map.

### 2.4 ~90 atoms are edge-less, load the note list too

Only **182 distinct node IDs appear in the 619 triples**, but the vault holds
~272 graph notes. That means **~90 concept atoms currently have no edges** and
will simply not exist in a graph built from triples alone. `analyze_kg.py`
already surfaces this as `orphan_nodes`. If a figure or analysis should reflect
the *whole* library (not just the connected part), **load the note list as
standalone nodes** (parse `kg.id`/`kg.type`/`title` from the note frontmatter,
or reuse `kg_common.NoteIndex`) and add any missing ones to the graph before
rendering. For pure connectivity/centrality analysis, the edge-induced subgraph
is fine, just state which view a given figure represents.

---

## 3. Graph cores compared

All four can ingest our triples. The question is fidelity, maintenance, and
whether we ever need more than networkx at this scale (~310 logical edges).

| Core | Latest (verified) | Multigraph + edge attrs | Drop-in load from our triples | Analysis depth | Install | License | Verdict |
|------|------|------|------|------|------|------|---------|
| **networkx** | 3.6.1 stable (2025-12-08); 3.7rc dev (2026-04-09) [1] | `MultiDiGraph`, first-class parallel typed edges + arbitrary attrs | `from_pandas_edgelist(..., create_using=MultiDiGraph, edge_key=...)` keeps every column | Native centrality, **native `louvain_communities` and `leiden_communities`** [5], paths, components, k-core | `pip`, pure-Python | BSD-3 | **Recommended core** |
| **igraph (python-igraph)** | actively maintained; native `community_leiden` since 0.8 [2] | Multigraph yes; attrs via vertex/edge attribute dicts | Needs an explicit edge-list build; less ergonomic from a triple frame | Very fast; native Leiden but **undirected + CPM/modularity only** [2] | `pip` wheels (C core) | GPL-2 | **Fallback for scale** |
| **rustworkx** | 0.17.1 [3] | Multigraph yes; **not a drop-in** networkx replacement; converts to/from networkx [3] | Convert via `rustworkx.networkx_converter` | 3×–100× faster than networkx [3]; smaller algorithm surface | `pip` wheels (Rust) | Apache-2.0 | Overkill at our scale |
| **graph-tool** | C++/Boost; conda-only | Multigraph + property maps, excellent | Manual build of the graph from columns | Fastest + deep statistical models (SBM) | **No pip**, Boost/CGAL/expat, conda or source [4] | LGPL-3 | Install friction not worth it here |

**Why networkx wins for us specifically:** our load source is a flat triple frame
with named columns, and `networkx.from_pandas_edgelist` maps those columns onto
edge attributes in one call while `create_using=nx.MultiDiGraph` preserves the
parallel typed edges. igraph/rustworkx/graph-tool all require us to hand-build the
edge list and re-attach attributes, buying performance we do not need at ~182
connected nodes / ~310 logical edges. Keep igraph+leidenalg in our back pocket purely as a
speed/quality fallback for Leiden if the graph grows an order of magnitude.

> **Leiden correction (verified, not assumed):** networkx now ships
> `nx.community.leiden_communities` *natively* alongside `louvain_communities`
> [5], so we do **not** need `leidenalg`/`igraph` just to run Leiden. Caveat:
> both Louvain and Leiden treat the graph as **undirected and weighted** and
> operate on a simple-graph projection, our typed multigraph must be projected
> (collapse parallel edges to a weight, or run community detection on a single
> edge-type subgraph) before clustering. That projection is an analysis choice to
> document, not a tool limitation.

---

## 4. Notebook-interactive renderers compared (the fidelity-critical tier)

This is the most important table in the doc. **Edge-attribute + parallel-typed-
edge fidelity is a first-class column**, because several popular renderers
silently flatten our multigraph and throw away edge types.

| Renderer | Latest / maintenance (verified) | Parallel typed edges | Per-edge attr binding (confidence/status/evidence) | Node-type color | Static export | Learning curve | License | Verdict |
|----------|------|------|------|------|------|------|------|---------|
| **ipysigma** | 0.23.0+ on PyPI; medialab/Sciences-Po, actively maintained [6] | **Preserves** (sigma.js/graphology multigraph model) | Rich `*_mapping` / `*_palette` / `*_range` kwargs for edge color/size/type/label [6] | `node_color` from a categorical attr | **Yes**, `.to_html()` standalone | Low–medium | MIT | **PRIMARY pick** |
| **yfiles-jupyter-graphs** | 1.10.7; yWorks, maintained [7] | Preserves (full edge objects) | Callable color/edge mappings returning CSS [7] | Yes, via mapping callable | In-widget export | Medium | **Proprietary (free to use, not OSS)** | **Strong runner-up; license caveat** |
| **plotly graph_objects** | maintained (core plotly) | **Manual**, you build edge traces yourself; parallel edges only if you draw them | Full control (you author hover/text/color per trace) | Yes (you author it) | **Yes**, HTML + PNG/SVG/PDF [8] | Medium–high (low-level) | MIT | **Publication-interactive pick** |
| **ipycytoscape** | 1.3.3; **maintenance Inactive** (no PyPI release in 12 mo) [9] | **Drops** parallel edges in multidigraphs (issue #191) [9] | Cytoscape style JSON | Yes | Limited | Medium | MIT | **Reject** (inactive + flattens) |
| **pyvis** | 0.3.2; **no release in 12 mo, effectively discontinued** [10] | **Drops**, does not support `MultiDiGraph`, keeps only the first edge [11] | Limited | Partial | HTML only | Low | BSD | **Reject** (discontinued + flattens, the classic offender) |
| **nx-altair** | 0.4.14 (2026-01-14) but project **Inactive**, ~322 weekly downloads [12] | No real multigraph model (chart-based) | Altair encodings on a flattened layout | Via encoding | Altair HTML/PNG/SVG | Low–medium | MIT | **Niche only** (small static interactive charts) |
| **graphistry (pygraphistry)** | maintained; **GPU + account required** [13] | Preserves | Rich, GPU-rendered | Yes | Hosted view | Low (API) but infra-heavy | BSD client / **hosted service** | **Reject for this repo** (uploads data to remote GPU hub; offline research vault) |

### 4.1 The disqualifier explained

`pyvis` and `ipycytoscape` both **collapse parallel edges**: when two typed edges
exist between the same node pair, they keep the first and drop the rest [9][11].
For us that means a paper that `uses` *and* `evaluates_on` the same dataset would
render as a single untyped line, the edge-type signal, which is the whole point
of our typed graph, is destroyed at render time. Combined with both being
unmaintained (no PyPI release in 12 months [9][10]), they are rejected despite
their popularity in older tutorials.

### 4.2 Why ipysigma is the primary pick

- Built specifically to render **networkx** (and igraph) graphs inside Jupyter,
  on sigma.js + graphology, which have a true multigraph model, parallel typed
  edges survive [6].
- Visual-channel binding is exactly our need: `node_color` (+ `node_color_palette`)
  for node **type** and `edge_color` (+ palette) for edge **type**, the two
  channels our data populates today. Numeric `*_range` mappings can later bind
  **confidence** (e.g. opacity/size) once it is densely populated [6]; today
  ~83% of edges have empty confidence, so it is an *if-present* overlay, not the
  primary encoding (see §2.1).
- `.to_html()` produces a **standalone interactive HTML file**, that is the
  bridge to "presentation" without leaving the notebook, and it is the natural
  hand-off artifact to the web/shareable track (`preparer-web`).
- MIT-licensed and actively maintained by a research lab (médialab), which fits a
  research repo better than a proprietary or hosted-service option.

### 4.3 Why graphistry is rejected *here*

graphistry is genuinely excellent for large graphs, but its visual server
**requires an account and uploads the graph to Graphistry Hub (or a self-hosted
GPU server)** [13]. For a research vault whose provenance and unpublished-paper
notes should stay local, shipping the graph to a third-party GPU service is the
wrong default. Note it as a "if we ever need 100k+ node GPU rendering" escape
hatch only.

---

## 5. Analysis layer, what to add beyond `analyze_kg.py`

All of the following run on the graph we load; none are in `analyze_kg.py` today.
Verified API names from networkx docs [5].

> **Run centrality/community/component analysis on the inverse-pair-DEDUPED,
> usually undirected projection** (§2.3), not on the raw 619-edge `MultiDiGraph`,
> otherwise the doubled graph skews every result. Run lineage tracing on the
> directed graph (direction is the point there).

- **Centrality (structural importance beyond raw degree):**
  `nx.betweenness_centrality` (brokers between research sub-areas),
  `nx.eigenvector_centrality_numpy`, `nx.pagerank` (default `weight="weight"`),
  `nx.katz_centrality`. These answer "which *concepts* anchor the literature
  graph", which degree ranking alone cannot.
- **Community detection:** `nx.community.louvain_communities` and
  `nx.community.leiden_communities` [5], find clusters of co-studied concepts
  (e.g. a "calibration" cluster vs an "abstention" cluster). Run on a projected
  simple graph (see §3 Leiden caveat).
- **Lineage / ancestry tracing (domain-specific, high value):** restrict to the
  lineage edge types from `library/SCHEMA.md`
  (`derived_from`, `variation_of`, `required_by`) and run
  `nx.ancestors` / `nx.descendants` / `nx.shortest_path` /
  `nx.all_simple_paths` on that **edge-type subgraph**. This gives method
  genealogies (e.g. the ancestry chain into DPO/KTO) that the flat degree report
  cannot express.
- **Structure:** `nx.weakly_connected_components`,
  `nx.strongly_connected_components`, `nx.k_core`, articulation points, to find
  isolated literature pockets and cut-vertices.

**Recommendation on duplication:** do **not** re-compute edge-type histograms,
degree, orphans, or unresolved targets, call `analyze_kg.py --json` and load its
output for those. The notebook stack adds the *graph-theoretic* layer on top.

---

## 6. Load path from `export_kg.py` output (sketch, doc only, no repo code)

Snippet illustrates the load contract only; per the mission, **no code file is
added to the repo**. Generate the export first:

```bash
python3 .agents/skills/knowledge-graph/scripts/export_kg.py \
    --root library --format json --output /tmp/eh-kg.json
```

Then, in a notebook:

```python
import json, networkx as nx

rows = json.load(open("/tmp/eh-kg.json"))   # 619 triple dicts (= ~310 logical edges)

def nid(label, _id):                # match analyze_kg.py node_key(value, fallback)
    return _id or label

# --- (1) DEDUPE INVERSE PAIRS (§2.3) -------------------------------------
# The ontology stores reciprocal edges; keep only the canonical direction so
# the graph is not doubled. Drop the inverse ("*_by") half; project the rest.
INVERSE = {"proposed_by": "proposes", "supported_by": "supports"}  # extend per edge-ontology.yaml
canon_rows = [r for r in rows if r["edge_type"] not in INVERSE]    # ~310 rows

# --- (2) DIRECTED MULTIGRAPH for lineage / direction-aware views ----------
G = nx.MultiDiGraph()
for r in canon_rows:                # nodes carry type so the renderer can color by it
    G.add_node(nid(r["source"], r["source_id"]), label=r["source"], ntype=r["source_type"])
    G.add_node(nid(r["target"], r["target_id"]), label=r["target"],
               ntype=r["target_type"], unresolved=(r["target_path"] == ""))
for r in canon_rows:                # key=edge_type keeps PARALLEL typed edges distinct (fidelity)
    G.add_edge(
        nid(r["source"], r["source_id"]), nid(r["target"], r["target_id"]),
        key=r["edge_type"], edge_type=r["edge_type"],
        confidence=r["confidence"] or None,   # SPARSE: 104 high / 515 empty today (§2.1)
        status=r["status"] or None,           # SPARSE: empty on all rows today
        evidence=r["evidence"] or None,       # SPARSE: empty on all rows today
        start=r["start"] or None, end=r["end"] or None,
        weight={"high": 1.0, "medium": 0.6, "low": 0.3}.get(r["confidence"], 1.0),
    )

# --- (3) ADD EDGE-LESS ATOMS so the whole library appears (§2.4) ----------
# ~90 of ~272 atoms have no edges; load the note list to include them.
from kg_common import NoteIndex                      # reuse the skill's own indexer
for note in NoteIndex.build("library").by_id.values():
    key = note.kg_id or note.title
    if key not in G:
        G.add_node(key, label=note.title, ntype=note.kg_type, edgeless=True)

# --- (4) UNDIRECTED PROJECTION for centrality / community / components -----
UG = nx.Graph(G)        # collapses reciprocal directions to single undirected edges

# render: node color = type, edge color = type (the channels our data populates)
from ipysigma import Sigma
Sigma(G, node_color="ntype", edge_color="edge_type").to_html("kg.html")
```

Notes:
- **`INVERSE` dedup (step 1) is the correctness step**, without it every metric
  runs on a doubled graph. Populate `INVERSE` from the reciprocal pairs in
  `.agents/skills/knowledge-graph/references/edge-ontology.yaml`.
- `MultiDiGraph` + `key=edge_type` stops the parallel-edge collapse that
  disqualifies pyvis/ipycytoscape.
- Run centrality/community on **`UG`** (deduped, undirected); run lineage tracing
  on **`G`** (direction matters).
- Edge metadata is written as `... or None` because `status`/`evidence` are empty
  today and most `confidence` values are empty, store them only when present.
- `weight` defaults to `1.0` (not a guessed mid-value) since most edges have no
  confidence; revisit once confidence is densely populated.
- Step 3 makes the figure represent the *whole* library; omit it for pure
  connectivity/centrality work on the edge-induced subgraph.
- `pandas` users can build `G` with
  `nx.from_pandas_edgelist(df_canon, "source_id", "target_id", edge_attr=[...],
  create_using=nx.MultiDiGraph, edge_key="edge_type")` after the inverse-pair filter.

---

## 7. Kùzu, NOT recommended (cautionary note only)

**Bottom line: do not adopt Kùzu.** It was the obvious embeddable Cypher/graph-DB
candidate, but it is now an abandoned project, and we do not need an embedded
graph-DB anyway.

What it *was*: an embeddable C++ property-graph database with a Python API,
Cypher, and zero-copy export of a queried subgraph to a networkx `DiGraph` plus
other Python GDS packages [14][15]. Variable-length path queries
(`MATCH (a)-[:derived_from*]->(b)`) read more cleanly in Cypher than hand-rolled
networkx traversals.

Why it is out: **Kùzu Inc was acquired by Apple (~Oct 9 2025)**; the open-source
KuzuDB repo (MIT) was **archived on GitHub (~Oct 10 2025)**, the website taken
down, and the maintainers dropped it [16][17]. This is exactly the decay-prone
external surface the +1 uncertainty posture anticipated. The community forked it,
**Kineviz "bighorn"** is seeking co-maintainers [17], but that is an early fork,
not a maintained product.

Why we do not need it regardless: at ~310 logical edges, networkx
`ancestors`/`descendants`/`all_simple_paths` over the lineage edge-type subgraph
(§5) already covers our lineage tracing. There is no scale or query-ergonomics
case strong enough to justify taking on an archived dependency.

If an embedded queryable store is ever genuinely needed, **re-verify at decision
time** and evaluate the `bighorn` fork (or alternatives such as DuckDB's property-
graph extension) then, do not assume Kùzu is viable. `preparer-web` reached the
same conclusion independently and likewise excludes it; `bighorn` and PyGraphistry
are the only web↔Python crossover points between our two docs.

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Inverse-pair edges double the graph** (619 rows ≈ 310 logical edges) | **High if unhandled** (the export does this by default) | **High** (skews every centrality/community/component metric) | Dedupe inverse pairs before analysis (§2.3); analyze the deduped undirected projection `UG`, trace lineage on directed `G` |
| **Edge metadata is sparse** (confidence 104/619; status & evidence empty) | High (current state) | Medium (visual encodings keyed on them show nothing) | Lead visuals with node-type color + edge-type; bind confidence/status/evidence *if-present* only; re-check populated fraction at adoption |
| **~90 atoms are edge-less** and vanish from triple-only graphs | High (current state) | Low-Medium (whole-library figures look incomplete) | Load the note list as standalone nodes (§2.4) when a figure should reflect the full library |
| Renderer flattens typed parallel edges (loses edge-type signal) | Medium (default for pyvis/ipycytoscape) | High | Use `MultiDiGraph` + `ipysigma`; treat parallel-edge fidelity as an acceptance test before adopting any renderer |
| Library landscape decays (a pick goes unmaintained) | Medium-High (already true for pyvis, ipycytoscape, nx-altair, **and Kùzu**) | Medium | networkx + ipysigma both actively maintained as of 2026-06; re-check at adoption; keep igraph as a documented fallback |
| Kùzu archived (was the embedded-DB candidate) | Certain | Low (now excluded, not adopted) | Excluded entirely (§7); networkx traversal covers lineage; re-evaluate bighorn/DuckDB-PGQ only if a store is later needed |
| yfiles license (proprietary) constrains redistribution | Low | Medium | Free to use but not OSS, prefer MIT ipysigma as primary; use yfiles only if its layout quality is needed |
| Community detection silently mis-models the directed multigraph | Medium | Medium | Document the undirected/weighted projection explicitly; run on edge-type subgraphs where direction matters |
| graphistry uploads vault data off-machine | (only if chosen) | High | Rejected as default; note as GPU escape-hatch only |

---

## 9. Recommendation (ranked, final)

1. **Core:** `networkx` `MultiDiGraph`, loaded via the §6 path **with inverse-pair
   dedup (§2.3)**. BSD-3, pure-pip, 1:1 fidelity with our 14-field export, native
   Louvain + Leiden.
2. **Interactive notebook renderer:** `ipysigma`, node color = node type, edge
   color = edge type (the channels our data populates today); `.to_html()` for
   sharing. Bind confidence as an *if-present* overlay once it is densely filled.
3. **Publication figure:** `matplotlib`/`netgraph` for static vector (paper) and
   `plotly` graph_objects when an interactive HTML figure is warranted.
4. **Analysis:** networkx centrality + community + lineage path-tracing
   (§5) on the **deduped** graph, layered **on top of** `analyze_kg.py` (call its
   `--json` output for the degree/orphan/edge-type basics rather than recomputing).
5. **Optional / later:** `igraph`+`leidenalg`, speed fallback **only** if the
   graph grows an order of magnitude. (No embedded graph-DB: Kùzu is dead, §7.)

**Do not adopt:** pyvis, ipycytoscape (both flatten parallel edges *and* are
unmaintained); graphistry as a default (off-machine data); graph-tool (install
friction unjustified at our scale); **Kùzu** (abandoned, §7).

This stack needs **zero compiled-from-source dependencies**, preserves every
typed edge from `export_kg.py` end-to-end (after inverse-pair dedup), encodes the
edge metadata that is actually populated, and cleanly extends, rather than
duplicates, `analyze_kg.py`.

---

## 10. References (dated; re-verify before pinning)

1. NetworkX latest/releases, https://networkx.org/documentation/latest/ ; https://github.com/networkx/networkx/releases (3.6.1 stable 2025-12-08; 3.7rc 2026-04-09)
2. python-igraph Leiden (`community_leiden`, undirected/CPM/modularity), https://igraph.org/python/ ; https://github.com/vtraag/leidenalg
3. rustworkx 0.17.1, networkx interop, multigraph, perf, https://www.rustworkx.org/ ; https://www.rustworkx.org/networkx.html
4. graph-tool install (Boost/CGAL/expat, conda, no pip), https://graph-tool.skewed.de/installation.html
5. NetworkX algorithms, community (`louvain_communities`, `leiden_communities`) and centrality (`betweenness_centrality`, `eigenvector_centrality`, `pagerank`, `katz_centrality`), https://networkx.org/documentation/stable/reference/algorithms/community.html ; https://networkx.org/documentation/stable/reference/algorithms/centrality.html (via Context7 `/networkx/networkx`)
6. ipysigma (medialab), edge color/size/type mappings, networkx/igraph, MIT, https://github.com/medialab/ipysigma ; https://pypi.org/project/ipysigma/
7. yFiles Graphs for Jupyter 1.10.7 (networkx importer, color mappings, proprietary-free), https://pypi.org/project/yfiles-jupyter-graphs/ ; https://yworks.github.io/yfiles-jupyter-graphs/
8. Plotly network graphs (go.Scatter edges, HTML/PNG/SVG export), https://plotly.com/python/network-graphs/
9. ipycytoscape 1.3.3, maintenance Inactive, parallel-edge bug #191, https://github.com/cytoscape/ipycytoscape ; https://github.com/QuantStack/ipycytoscape/issues/191 ; https://snyk.io/advisor/python/ipycytoscape
10. pyvis 0.3.2, no release in 12 mo (discontinued), https://pypi.org/project/pyvis/ ; https://snyk.io/advisor/python/pyvis
11. pyvis drops parallel edges / no MultiDiGraph support, https://github.com/WestHealth/pyvis/issues/51
12. nx-altair 0.4.14 (2026-01-14) but Inactive, https://pypi.org/project/nx-altair/ ; https://snyk.io/advisor/python/nx-altair
13. PyGraphistry account + GPU hub requirement, https://github.com/graphistry/pygraphistry ; https://pygraphistry.readthedocs.io/en/latest/install/server.html
14. Kùzu Python / networkx export, https://pypi.org/project/kuzu/ ; https://kuzudb.github.io/docs/tutorials/
15. Kùzu zero-copy export to Python GDS / networkx DiGraph, https://thedataquarry.com/blog/embedded-db-2/
16. Apple acquires Kùzu (Oct 2025), https://betakit.com/apple-strikes-deal-to-acquire-canadian-database-software-startup-kuzu/ ; https://www.macrumors.com/2026/02/11/apple-acquires-new-database-app/
17. KuzuDB OSS abandoned; Kineviz "bighorn" fork, https://www.theregister.com/2025/10/14/kuzudb_abandoned/

---

## Appendix: Cross-track coordination

- **Shared tool (Kùzu), both tracks EXCLUDE it.** The Apple-acquisition /
  archived-repo finding was found independently on both sides and relayed between
  us; my doc excludes it on the programmatic axis (§7), `preparer-web` excludes it
  on the browser/shareable axis. The only remaining web↔Python crossover points
  are the `bighorn` fork (if an embedded store is ever needed) and PyGraphistry.
- **Hand-off artifact:** `ipysigma.to_html()` is the natural bridge between this
  notebook stack and the web/shareable track, a self-contained interactive HTML
  the web track can host or embed.
